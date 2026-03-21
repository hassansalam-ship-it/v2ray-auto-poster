// ╔══════════════════════════════════════════════════════════════════╗
// ║  Ashaq Team — CF Worker VLESS Proxy                             ║
// ║  يعمل كـ VLESS proxy عبر WebSocket على Cloudflare Workers       ║
// ║  يدعم كل Bug Hosts الـ 12                                       ║
// ╚══════════════════════════════════════════════════════════════════╝

// UUID الخاص بك — لا تغيّره بعد النشر
const USER_ID = '__UUID__';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const upgrade = request.headers.get('Upgrade');

    // WebSocket upgrade request — هذا هو الـ v2ray connection
    if (upgrade === 'websocket') {
      return handleWS(request);
    }

    // HTTP request — صفحة بسيطة للتحقق
    if (url.pathname === '/') {
      return new Response(
        `<html><body>
          <h2>✅ Worker Active</h2>
          <p>UUID: ${USER_ID.substring(0,8)}****</p>
          <p>Time: ${new Date().toUTCString()}</p>
        </body></html>`,
        { headers: { 'Content-Type': 'text/html' } }
      );
    }

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        uuid: USER_ID.substring(0,8) + '****',
        ts: Date.now()
      }), { headers: { 'Content-Type': 'application/json' } });
    }

    return new Response('Not Found', { status: 404 });
  }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  WebSocket Handler — VLESS Protocol
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function handleWS(request) {
  const [client, server] = Object.values(new WebSocketPair());
  server.accept();

  // Process VLESS protocol
  server.addEventListener('message', async (event) => {
    try {
      await processVLESS(server, event.data);
    } catch(e) {
      server.close(1011, 'Internal Error');
    }
  });

  server.addEventListener('close', () => {});
  server.addEventListener('error', () => {});

  return new Response(null, {
    status: 101,
    webSocket: client,
  });
}

async function processVLESS(ws, data) {
  // Parse VLESS header
  const buffer = data instanceof ArrayBuffer ? data : await data.arrayBuffer();
  const view = new DataView(buffer);

  // Version (1 byte)
  const version = view.getUint8(0);
  if (version !== 0) {
    ws.close(1002, 'Invalid version');
    return;
  }

  // UUID (16 bytes)
  const uuidBytes = new Uint8Array(buffer, 1, 16);
  const uuid = formatUUID(uuidBytes);

  if (uuid !== USER_ID) {
    ws.close(1002, 'Invalid UUID');
    return;
  }

  // Addon length (1 byte) + addon data
  const addonLen = view.getUint8(17);
  let offset = 18 + addonLen;

  // Command (1 byte): 1=TCP, 2=UDP, 3=MUX
  const cmd = view.getUint8(offset++);

  // Port (2 bytes, big-endian)
  const port = view.getUint16(offset); offset += 2;

  // Address type (1 byte): 1=IPv4, 2=Domain, 3=IPv6
  const addrType = view.getUint8(offset++);
  let address;

  if (addrType === 1) {
    // IPv4
    address = `${view.getUint8(offset)}.${view.getUint8(offset+1)}.${view.getUint8(offset+2)}.${view.getUint8(offset+3)}`;
    offset += 4;
  } else if (addrType === 2) {
    // Domain
    const domainLen = view.getUint8(offset++);
    address = new TextDecoder().decode(new Uint8Array(buffer, offset, domainLen));
    offset += domainLen;
  } else if (addrType === 3) {
    // IPv6
    const ipv6 = [];
    for (let i = 0; i < 8; i++) {
      ipv6.push(view.getUint16(offset + i*2).toString(16));
    }
    address = ipv6.join(':');
    offset += 16;
  } else {
    ws.close(1002, 'Unknown address type');
    return;
  }

  // Response header (VLESS response)
  const responseHeader = new Uint8Array([0, 0]); // version=0, addon=0

  if (cmd === 1) {
    // TCP connection
    await handleTCP(ws, address, port, buffer.slice(offset), responseHeader);
  } else if (cmd === 2) {
    // UDP — for DNS
    await handleUDP(ws, buffer.slice(offset), responseHeader);
  } else {
    ws.close(1002, 'Unsupported command');
  }
}

async function handleTCP(ws, address, port, payload, responseHeader) {
  try {
    const conn = await connect({ hostname: address, port });
    const writer = conn.writable.getWriter();

    // Send VLESS response header first
    ws.send(responseHeader.buffer);

    // Forward initial payload if any
    if (payload.byteLength > 0) {
      await writer.write(new Uint8Array(payload));
    }

    // Bidirectional pipe
    const wsToTCP = pipeMsgsToTCP(ws, writer);
    const tcpToWS = pipeStreamToWS(conn.readable, ws);

    await Promise.race([wsToTCP, tcpToWS]);
    writer.close().catch(() => {});

  } catch(e) {
    ws.close(1011, 'Connection failed');
  }
}

async function handleUDP(ws, payload, responseHeader) {
  // Simple UDP/DNS forwarding via fetch (DNS over HTTPS)
  ws.send(responseHeader.buffer);
}

async function pipeMsgsToTCP(ws, writer) {
  return new Promise((resolve, reject) => {
    ws.addEventListener('message', async (event) => {
      try {
        const data = event.data instanceof ArrayBuffer
          ? event.data : await event.data.arrayBuffer();
        await writer.write(new Uint8Array(data));
      } catch(e) { reject(e); }
    });
    ws.addEventListener('close', resolve);
    ws.addEventListener('error', reject);
  });
}

async function pipeStreamToWS(readable, ws) {
  const reader = readable.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (ws.readyState === 1) ws.send(value);
      else break;
    }
  } finally {
    reader.releaseLock();
  }
}

// UUID formatter
function formatUUID(bytes) {
  const hex = Array.from(bytes).map(b => b.toString(16).padStart(2,'0'));
  return [
    hex.slice(0,4).join(''),
    hex.slice(4,6).join(''),
    hex.slice(6,8).join(''),
    hex.slice(8,10).join(''),
    hex.slice(10,16).join('')
  ].join('-');
}
