addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
  });
  
  async function handleRequest(request) {
    const url = new URL(request.url);
    const api = await fetch('https://api.npoint.io/4fe091fefa5b91378f02')
    const data = await api.json()
    url.hostname = data['DLServer1']['hostname']; // Replace 'example.com' with the target hostname.
    url.protocol = 'https';
    const proxyRequest = new Request(url, {
        method: request.method,
        headers: request.headers,
        body: request.body,
        redirect: 'follow'
    });
    proxyRequest.headers.set('x-custom-header', 'value');
    const response = await fetch(proxyRequest);
    let newResponse = new Response(response.body, response);
    newResponse.headers.set('x-added-header', 'header value');
    return newResponse;
  }