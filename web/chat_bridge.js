/* Browser-only transport. Credentials and model configuration stay on the server. */
(() => {
  const responses = new Map();
  let counter = 0;
  let demoConsumed = false;
  window.chessCorpDemoSession = () => {
    if(demoConsumed)return '';
    demoConsumed=true;
    const session = new URLSearchParams(location.search).get('demo_session') || '';
    return /^demo_[a-f0-9]{32}$/.test(session) ? session : '';
  };
  // The Emscripten FFI is byte-oriented. Escape Unicode on both JSON boundaries.
  const encodeResponse = (value) => JSON.stringify(value).replace(/[-￿]/g,
    char => '\\u' + char.charCodeAt(0).toString(16).padStart(4, '0'));
  window.chessCorpRequestSend = (encoded, path) => {
    if (!["/api/chat","/api/director","/api/director/execution","/api/director/jobs","/api/director/jobs/execution","/api/assets/updates","/api/world/plan","/api/world/execution","/api/world/presence"].includes(path)) throw new Error("Invalid endpoint");
    const id = String(++counter);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 35000);
    fetch(path, {
      method: 'POST', headers: {'Content-Type': 'application/json','X-Chess-Language':window.chessCorpGetLanguage?.()??'en'},
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
  window.chessCorpChatSend = encoded => window.chessCorpRequestSend(encoded, '/api/chat');
  window.chessCorpChatPoll = (id) => {
    const result = responses.get(String(id)) || '';
    if (result) responses.delete(String(id));
    return result;
  };
})();
