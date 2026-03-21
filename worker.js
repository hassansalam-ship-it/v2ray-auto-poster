// ╔══════════════════════════════════════════════════════════════════╗
// ║  Ashaq Team — CF Worker VLESS Proxy v2                          ║
// ║  Compatible with Cloudflare Workers (no ES modules)             ║
// ╚══════════════════════════════════════════════════════════════════╝

const USER_ID = '__UUID__';

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const upgrade = request.headers.get('Upgrade');

  // WebSocket — v2ray connection
  if (upgrade === 'websocket') {
    return handleWS(request);
  }

  // Health check
  if (url.pathname === '/health') {
    return new Response(JSON.stringify({
      status: 'ok',
      ts: Date.now()
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // Default page
  return new Response(
    '<html><body><h2>OK</h2></body></html>',
    { headers: { 'Content-Type': 'text/html' } }
  );
}

async function handleWS(request) {
  const pair = new WebSocketPair();
  const [client, server] = Object.values(pair);
  server.accept();

  server.addEventListener('message', async (event) => {
    try {
      await processVLESS(server, event.data);
    } catch(e) {
      try { server.close(1011, 'Error'); } catch(e2) {}
    }
  });

  server.addEventListener('error', () => {});
  server.addEventListener('close', () => {});

  return new Response(null, {
    status: 101,
    webSocket: client,
  });
}

async function processVLESS(ws, data) {
  const buffer = data instanceof ArrayBuffer ? data : await new Response(data).arrayBuffer();
  const view = new DataView(buffer);

  const version = view.getUint8(0);
  if (version !== 0) { ws.close(1002, 'Bad version'); return; }

  // UUID check (bytes 1-16)
  const uuidBytes = new Uint8Array(buffer, 1, 16);
  const uuid = bytesToUUID(uuidBytes);
  if (uuid.toLowerCase() !== USER_ID.toLowerCase()) {
    ws.close(1002, 'Bad UUID');
    return;
  }

  // Skip addon
  const addonLen = view.getUint8(17);
  let offset = 18 + addonLen;

  // Command
  const cmd = view.getUint8(offset++);

  // Port
  const port = view.getUint16(offset); offset += 2;

  // Address
  const addrType = view.getUint8(offset++);
  let address = '';

  if (addrType === 1) {
    address = `${view.getUint8(offset)}.${view.getUint8(offset+1)}.${view.getUint8(offset+2)}.${view.getUint8(offset+3)}`;
    offset += 4;
  } else if (addrType === 2) {
    const len = view.getUint8(offset++);
    address = new TextDecoder().decode(new Uint8Array(buffer, offset, len));
    offset += len;
  } else if (addrType === 3) {
    const parts = [];
    for (let i = 0; i < 8; i++) parts.push(view.getUint16(offset + i*2).toString(16));
    address = parts.join(':');
    offset += 16;
  } else {
    ws.close(1002, 'Bad addr type');
    return;
  }

  const payload = buffer.slice(offset);
  const responseHeader = new Uint8Array([0, 0]);

  if (cmd === 1) {
    await handleTCP(ws, address, port, payload, responseHeader);
  } else {
    ws.close(1002, 'Unsupported cmd');
  }
}

async function handleTCP(ws, address, port, payload, responseHeader) {
  try {
    const conn = await connect({ hostname: address, port: port });
    const writer = conn.writable.getWriter();

    ws.send(responseHeader.buffer);

    if (payload.byteLength > 0) {
      await writer.write(new Uint8Array(payload));
    }

    // Pipe WS → TCP
    ws.addEventListener('message', async (event) => {
      try {
        const d = event.data instanceof ArrayBuffer
          ? event.data : await new Response(event.data).arrayBuffer();
        await writer.write(new Uint8Array(d));
      } catch(e) {}
    });

    ws.addEventListener('close', () => {
      try { writer.close(); } catch(e) {}
    });

    // Pipe TCP → WS
    const reader = conn.readable.getReader();
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (ws.readyState === 1) ws.send(value);
        else break;
      }
    } catch(e) {}
    finally {
      reader.releaseLock();
      try { ws.close(); } catch(e) {}
    }

  } catch(e) {
    try { ws.close(1011, 'Connect failed'); } catch(e2) {}
  }
}

function bytesToUUID(bytes) {
  const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0'));
  return [
    hex.slice(0,4).join(''),
    hex.slice(4,6).join(''),
    hex.slice(6,8).join(''),
    hex.slice(8,10).join(''),
    hex.slice(10,16).join('')
  ].join('-');
}
