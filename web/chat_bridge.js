/* Browser-only transport. Credentials and model configuration stay on the server. */
(() => {
  const responses = new Map();
  let counter = 0;
  // The Emscripten FFI is byte-oriented. Escape Unicode on both JSON boundaries.
  const encodeResponse = (value) => JSON.stringify(value).replace(/[-￿]/g,
    char => '\\u' + char.charCodeAt(0).toString(16).padStart(4, '0'));
  window.chessCorpChatSend = (encoded) => {
    const id = String(++counter);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 35000);
    fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: encoded, signal: controller.signal,
    }).then(async (response) => {
      let data;
      try { data = await response.json(); }
      catch { data = {detail: 'Backend jest niedostępny. Możesz kontynuować grę.'}; }
      responses.set(id, encodeResponse(response.ok ? data : {error: data.detail || 'Błąd połączenia z Buddy’m.'}));
    }).catch(() => {
      responses.set(id, encodeResponse({error: 'Brak połączenia z Buddy’m lub przekroczony czas. Spróbuj ponownie.'}));
    }).finally(() => clearTimeout(timer));
    return id;
  };
  window.chessCorpChatPoll = (id) => {
    const result = responses.get(String(id)) || '';
    if (result) responses.delete(String(id));
    return result;
  };
})();
