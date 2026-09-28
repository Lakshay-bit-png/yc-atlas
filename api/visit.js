// Visitor counter backed by Upstash Redis (connected through the Vercel Marketplace).
//
// POST { id, newVisit }  -> records the visitor, bumps visits if newVisit, returns totals
// GET                    -> returns totals only
//
// Keys:
//   yc:visits              total visits (one per browser session)
//   yc:visitors            set of anonymous browser ids (its size = unique visitors)
//   yc:visits:<date>       visits per UTC day
//   yc:visitors:<date>     unique visitors per UTC day (kept 400 days)
import { Redis } from '@upstash/redis';

const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
const redis = url && token ? new Redis({ url, token }) : null;

const ID = /^[a-zA-Z0-9-]{8,64}$/;
const DAY_TTL = 60 * 60 * 24 * 400;

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (!redis) return res.status(503).json({ error: 'Redis is not connected to this project' });

  try {
    if (req.method === 'POST') {
      const { id, newVisit } = req.body || {};
      if (!ID.test(id || '')) return res.status(400).json({ error: 'invalid visitor id' });
      const day = new Date().toISOString().slice(0, 10);
      const p = redis.pipeline();
      p.sadd('yc:visitors', id);
      p.sadd(`yc:visitors:${day}`, id);
      p.expire(`yc:visitors:${day}`, DAY_TTL);
      if (newVisit) {
        p.incr('yc:visits');
        p.incr(`yc:visits:${day}`);
      }
      await p.exec();
    } else if (req.method !== 'GET') {
      return res.status(405).json({ error: 'method not allowed' });
    }

    const [visits, visitors] = await Promise.all([redis.get('yc:visits'), redis.scard('yc:visitors')]);
    return res.status(200).json({ visits: Number(visits) || 0, visitors });
  } catch (err) {
    console.error('visit counter failed', err);
    return res.status(500).json({ error: 'counter unavailable' });
  }
}
