/** Base URL of the FastAPI backend, baked in at build time.

Locally it comes from packages/web/.env; on Vercel from the web project's
environment variables. */
export const API_URL: string = import.meta.env.VITE_API_URL as string;
if (!API_URL) throw new Error('VITE_API_URL was not set at build time');

/** Mirrors Cadence in packages/app/src/models/subscriber.py. */
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

/** One public wall card, display-ready — see WallDeal in packages/app/src/routers/deals.py. */
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

/** The form control each API field belongs to, so an error names what the
reader is looking at rather than the wire format. */
const FIELD_LABELS: Record<string, string> = {
	username: 'Username',
	email: 'Email',
	departure_airports: 'Departure cities',
	currency: 'Currency',
	min_nights: 'Minimum nights',
	max_nights: 'Maximum nights',
	min_days_ahead: 'Search from (days ahead)',
	max_days_ahead: 'Search to (days ahead)',
	cadence: 'Cadence',
	gem_count: 'Discoveries per email',
	favorite_countries: 'Favorite destinations',
	excluded_countries: 'Excluded countries'
};

/** Pydantic's phrasing rewritten for readers.

Every bound is carried over from the message itself, never restated here —
the backend stays the only place a limit is written down. Entries for
field errors read as fragments, completed by the field's label; entries for
whole-form errors, which carry no field, read as sentences. */
const REWRITES: [RegExp, string][] = [
	[/^Field required$/, 'is required.'],
	[/^Input should be greater than or equal to (\d+)$/, 'must be $1 or more.'],
	[/^Input should be less than or equal to (\d+)$/, 'must be $1 or less.'],
	[/^Input should be a valid integer.*/, 'must be a whole number.'],
	[/^List should have at least (\d+) item.*/, 'needs at least $1.'],
	[/^List should have at most (\d+) item.*/, 'takes at most $1.'],
	[/^String should have at least (\d+) character.*/, 'must be at least $1 characters.'],
	[/^String should have at most (\d+) character.*/, 'must be at most $1 characters.'],
	[/^value is not a valid email address.*/, 'must be a valid email address.'],
	[/^unknown currency$/, 'needs to be picked from the list.'],
	[/^unknown [^:]+: (.+)$/, 'has an entry that is not on the list: $1.'],
	[/^duplicate .+$/, 'has the same entry twice.'],
	[
		/^max_nights must be greater than min_nights$/,
		'Maximum nights must be more than minimum nights.'
	],
	[
		/^max_days_ahead must be greater than min_days_ahead$/,
		'Your search window has to end after it starts.'
	],
	[
		/^max_nights \((\d+)\) cannot exceed the search range duration \((\d+) days\)$/,
		'A trip of up to $1 nights does not fit in a $2-day search window. Widen the window or shorten the trip.'
	]
];

/** One API message, in plain English. Unrecognized messages pass through:
the backend's own `detail` strings already read as sentences. */
function readable(message: string): string {
	const text = message.replace(/^Value error, /, '');
	const rewrite = REWRITES.find(([pattern]) => pattern.test(text));
	return rewrite ? text.replace(rewrite[0], rewrite[1]) : text;
}

/** Flatten a FastAPI error body (422 detail list or plain detail) to messages
the reader can act on. */
export function errorMessages(body: unknown): string[] {
	const { detail } = body as FastApiError;
	if (typeof detail === 'string') return [readable(detail)];
	return detail.map((e) => {
		const label = FIELD_LABELS[e.loc.filter((part) => part !== 'body').join('.')];
		const message = readable(e.msg);
		return label ? `${label} ${message}` : message;
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
