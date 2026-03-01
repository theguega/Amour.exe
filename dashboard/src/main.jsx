import React from 'react';
import { createRoot } from 'react-dom/client';
import { ApolloClient, InMemoryCache, ApolloProvider } from '@apollo/client';
import App from './App.jsx';
import './index.css';

// Using a placeholder GraphQL URI for W&B Weave API
const weaveGqlUri = import.meta.env.VITE_WEAVE_GQL_URI || 'https://api.wandb.ai/graphql';

const client = new ApolloClient({
  uri: weaveGqlUri,
  cache: new InMemoryCache(),
});

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ApolloProvider client={client}>
      <App />
    </ApolloProvider>
  </React.StrictMode>
);
