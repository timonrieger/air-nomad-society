<script lang="ts">
	import { Popover } from 'bits-ui';
	import type { Snippet } from 'svelte';

	let {
		label,
		hint,
		required = false,
		children
	}: { label: string; hint?: string; required?: boolean; children: Snippet } = $props();
</script>

<label class="flex flex-col gap-1.5">
	<span class="flex items-center gap-1.5 text-sm text-ink-muted">
		{label}{#if required}<span class="-ml-1 text-accent-bright" aria-hidden="true">*</span>{/if}
		{#if hint}
			<!-- Popover, not Tooltip: opens on tap, so it works on touch screens. -->
			<Popover.Root>
				<Popover.Trigger
					type="button"
					aria-label="More about {label}"
					class="inline-flex cursor-help items-center text-ink-muted hover:text-ink"
				>
					<svg
						width="14"
						height="14"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
					>
						<circle cx="12" cy="12" r="10" />
						<line x1="12" y1="11" x2="12" y2="16" />
						<circle cx="12" cy="8" r="0.5" fill="currentColor" />
					</svg>
				</Popover.Trigger>
				<Popover.Portal>
					<Popover.Content class="tooltip" sideOffset={6}>{hint}</Popover.Content>
				</Popover.Portal>
			</Popover.Root>
		{/if}
	</span>
	{@render children()}
</label>
