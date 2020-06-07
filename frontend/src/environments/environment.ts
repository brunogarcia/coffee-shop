export const environment = {
  production: false,
  apiServerUrl: 'http://127.0.0.1:5000', // the running FLASK api server url
  auth0: {
    url: 'brunogarcia.eu', // the auth0 domain prefix
    audience: 'coffe-shop', // the audience set for the auth0 app
    clientId: 'tbK3jJHRFE760KT8CHaUPPgdiUKq9l6C', // the client id generated for the auth0 app
    callbackURL: 'http://localhost:8100', // the base url of the running ionic application. 
  }
};
