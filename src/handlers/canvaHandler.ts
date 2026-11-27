import { Context } from 'hono';
import { RouterError } from '../errors/RouterError';

/**
 * Canva API Handler
 * Provides design creation, template fetching, and design metadata endpoints
 */

const CANVA_API_BASE = 'https://api.canva.com/rest/v1';

interface CanvaConfig {
  clientId?: string;
  clientSecret?: string;
  bearerToken?: string;
}

/**
 * Get access token for Canva API
 */
async function getCanvaAccessToken(config: CanvaConfig): Promise<string> {
  if (config.bearerToken) {
    return config.bearerToken;
  }

  if (!config.clientId || !config.clientSecret) {
    throw new RouterError('Missing Canva credentials (clientId/clientSecret or bearerToken)');
  }

  const response = await fetch(`${CANVA_API_BASE}/oauth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: config.clientId,
      client_secret: config.clientSecret,
    }).toString(),
  });

  if (!response.ok) {
    throw new RouterError(`Failed to authenticate with Canva: ${response.statusText}`);
  }

  const data = await response.json() as any;
  return data.access_token;
}

/**
 * Handler for Canva design creation
 */
export async function canvaCreateDesignHandler(c: Context): Promise<Response> {
  try {
    const request = await c.req.json();
    const headers = Object.fromEntries(c.req.raw.headers);

    const config: CanvaConfig = {
      clientId: headers['x-canva-client-id'] || process.env.CANVA_CLIENT_ID,
      clientSecret: headers['x-canva-client-secret'] || process.env.CANVA_CLIENT_SECRET,
      bearerToken: headers['x-canva-bearer-token'] || process.env.CANVA_BEARER_TOKEN,
    };

    const token = await getCanvaAccessToken(config);

    const response = await fetch(`${CANVA_API_BASE}/designs`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { 'content-type': 'application/json' },
    });
  } catch (err: any) {
    console.error('Canva create design error:', err);
    return new Response(
      JSON.stringify({
        status: 'error',
        message: err.message || 'Failed to create design',
      }),
      { status: 500, headers: { 'content-type': 'application/json' } }
    );
  }
}

/**
 * Handler for fetching design templates
 */
export async function canvaGetTemplatesHandler(c: Context): Promise<Response> {
  try {
    const headers = Object.fromEntries(c.req.raw.headers);

    const config: CanvaConfig = {
      clientId: headers['x-canva-client-id'] || process.env.CANVA_CLIENT_ID,
      clientSecret: headers['x-canva-client-secret'] || process.env.CANVA_CLIENT_SECRET,
      bearerToken: headers['x-canva-bearer-token'] || process.env.CANVA_BEARER_TOKEN,
    };

    const token = await getCanvaAccessToken(config);

    const response = await fetch(`${CANVA_API_BASE}/design-templates`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { 'content-type': 'application/json' },
    });
  } catch (err: any) {
    console.error('Canva get templates error:', err);
    return new Response(
      JSON.stringify({
        status: 'error',
        message: err.message || 'Failed to fetch templates',
      }),
      { status: 500, headers: { 'content-type': 'application/json' } }
    );
  }
}

/**
 * Handler for fetching design metadata
 */
export async function canvaGetDesignHandler(c: Context): Promise<Response> {
  try {
    const designId = c.req.param('designId');
    if (!designId) {
      throw new RouterError('Missing designId parameter');
    }

    const headers = Object.fromEntries(c.req.raw.headers);

    const config: CanvaConfig = {
      clientId: headers['x-canva-client-id'] || process.env.CANVA_CLIENT_ID,
      clientSecret: headers['x-canva-client-secret'] || process.env.CANVA_CLIENT_SECRET,
      bearerToken: headers['x-canva-bearer-token'] || process.env.CANVA_BEARER_TOKEN,
    };

    const token = await getCanvaAccessToken(config);

    const response = await fetch(`${CANVA_API_BASE}/designs/${designId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { 'content-type': 'application/json' },
    });
  } catch (err: any) {
    console.error('Canva get design error:', err);
    return new Response(
      JSON.stringify({
        status: 'error',
        message: err.message || 'Failed to fetch design',
      }),
      { status: 500, headers: { 'content-type': 'application/json' } }
    );
  }
}

/**
 * Handler for listing user's designs
 */
export async function canvaListDesignsHandler(c: Context): Promise<Response> {
  try {
    const headers = Object.fromEntries(c.req.raw.headers);

    const config: CanvaConfig = {
      clientId: headers['x-canva-client-id'] || process.env.CANVA_CLIENT_ID,
      clientSecret: headers['x-canva-client-secret'] || process.env.CANVA_CLIENT_SECRET,
      bearerToken: headers['x-canva-bearer-token'] || process.env.CANVA_BEARER_TOKEN,
    };

    const token = await getCanvaAccessToken(config);

    const response = await fetch(`${CANVA_API_BASE}/designs`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { 'content-type': 'application/json' },
    });
  } catch (err: any) {
    console.error('Canva list designs error:', err);
    return new Response(
      JSON.stringify({
        status: 'error',
        message: err.message || 'Failed to list designs',
      }),
      { status: 500, headers: { 'content-type': 'application/json' } }
    );
  }
}
