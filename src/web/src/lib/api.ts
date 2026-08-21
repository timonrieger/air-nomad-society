/** Base URL of the FastAPI backend, baked in at build time.

Locally it comes from the repo-root .env (vite's envDir points there);
on Vercel from the web project's environment variables. */
export const API_URL: string = import.meta.env.VITE_API_URL as string;
if (!API_URL) throw new Error('VITE_API_URL was not set at build time');

/** Mirrors Cadence in src/app/models/subscriber.py. */
export type Cadence = 'weekly' | 'biweekly' | 'monthly';

export type RefData = {
	cities: { city: string; code: string }[];
	currencies: string[];
	countries: string[];
	regions: Record<string, string[]>;
};

export type Subscription = {
	username: string;
	email: string;
	departure_airports: string[];
	currency: string;
	min_nights: number;
	max_nights: number;
	min_days_ahead: number;
	max_days_ahead: number;
	cadence: Cadence;
	gem_count: number;
	favorites: string[];
	excluded: string[];
};

/** Request body for POST /subscribe and PUT /subscription. */
export type SubscriptionIn = {
	username: string;
	email: string;
	departure_airports: string[];
	currency: string;
	min_nights: number;
	max_nights: number;
	min_days_ahead: number;
	max_days_ahead: number;
	cadence: Cadence;
	gem_count: number;
	favorite_countries: string[];
	excluded_countries: string[];
};

/** Form bounds mirroring SubscriptionIn in src/app/routers/subscriptions.py. */
export const LIMITS = {
	usernameMin: 3,
	usernameMax: 20,
	maxDaysAhead: 365,
	gemCountMax: 10
} as const;

/** One public wall card, display-ready — see WallDeal in src/app/routers/deals.py. */
export type WallDeal = {
	destination: string;
	departure_city: string;
	price: number;
	currency: string;
	savings_percent: number | null;
	usual_price: number | null;
	badge: string | null;
	found_on: string;
	link: string;
	image_url: string;
};

export function tokenFromUrl(): string | null {
	return new URLSearchParams(location.search).get('token');
}

type FastApiError = { detail: string | { loc: (string | number)[]; msg: string }[] };

/** Flatten a FastAPI error body (422 detail list or plain detail) to messages. */
export function errorMessages(body: unknown): string[] {
	const { detail } = body as FastApiError;
	if (typeof detail === 'string') return [detail];
	return detail.map((e) => {
		const field = e.loc.filter((part) => part !== 'body').join('.');
		return field ? `${field}: ${e.msg}` : e.msg;
	});
}

async function request(path: string, init?: RequestInit): Promise<{ ok: boolean; body: unknown }> {
	const response = await fetch(`${API_URL}${path}`, init);
	return { ok: response.ok, body: await response.json() };
}

export async function fetchRefData(): Promise<RefData> {
	return (await request('/refdata')).body as RefData;
}

export async function fetchDeals(): Promise<WallDeal[]> {
	return (await request('/deals')).body as WallDeal[];
}

/** Resolves to null when the token is invalid or the subscription no longer exists. */
export async function fetchSubscription(token: string): Promise<Subscription | null> {
	const { ok, body } = await request(`/subscription?token=${encodeURIComponent(token)}`);
	return ok ? (body as Subscription) : null;
}

/** Create (no token) or update (token) a subscription; resolves to error messages, empty on success. */
export async function saveSubscription(
	payload: SubscriptionIn,
	token: string | null
): Promise<string[]> {
	const path = token ? `/subscription?token=${encodeURIComponent(token)}` : '/subscribe';
	const { ok, body } = await request(path, {
		method: token ? 'PUT' : 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	});
	return ok ? [] : errorMessages(body);
}

/** The address an unsubscribe token belongs to; null when the link no longer resolves. */
export async function fetchUnsubscribeTarget(token: string): Promise<string | null> {
	const { ok, body } = await request(`/unsubscribe/target?token=${encodeURIComponent(token)}`);
	return ok ? (body as { email: string }).email : null;
}

/** Hit one of the token-actioned endpoints and flatten the response to messages.

Unsubscribing is a POST: it deletes the subscription for good, and a GET
would let any link prefetcher in the mail path fire it. */
export async function tokenAction(
	path: '/confirm' | '/unsubscribe',
	token: string
): Promise<{ ok: boolean; messages: string[] }> {
	const { ok, body } = await request(`${path}?token=${encodeURIComponent(token)}`, {
		method: path === '/unsubscribe' ? 'POST' : 'GET'
	});
	return { ok, messages: ok ? [(body as { detail: string }).detail] : errorMessages(body) };
}
