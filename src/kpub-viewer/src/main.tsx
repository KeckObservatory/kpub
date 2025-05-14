import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { ReactRouter6Adapter } from 'use-query-params/adapters/react-router-6';
import { QueryParamProvider } from 'use-query-params';
import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.Fragment>
    <React.StrictMode>
      <BrowserRouter>
        <QueryParamProvider adapter={ReactRouter6Adapter}>
          <App />
        </QueryParamProvider>
      </BrowserRouter>
    </React.StrictMode>
  </React.Fragment>
)

