/** Base URL of the FastAPI backend, baked in at build time. */
export const API_URL: string =
	(import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

export type RefData = {
	cities: { city: string; code: string }[];
	currencies: string[];
	countries: string[];
};

export type Subscription = {
	username: string;
	email: string;
	departure_iata: string;
	currency: string;
	min_nights: number;
	max_nights: number;
	min_days_ahead: number;
	max_days_ahead: number;
	favorites: string[];
	excluded: string[];
};

/** Flatten a FastAPI error body (422 detail list or plain detail) to messages. */
export function errorMessages(body: unknown): string[] {
	const detail = (body as { detail?: unknown })?.detail;
	if (typeof detail === 'string') return [detail];
	if (Array.isArray(detail)) {
		return detail.map((e: { loc?: (string | number)[]; msg?: string }) => {
			const field = e.loc?.filter((part) => part !== 'body').join('.');
			return field ? `${field}: ${e.msg}` : (e.msg ?? 'Invalid input');
		});
	}
	return ['Something went wrong. Please try again.'];
}
