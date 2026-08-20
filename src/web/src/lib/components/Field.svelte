<script lang="ts">
	import type { Snippet } from 'svelte';

	let { label, children }: { label: string; children: Snippet } = $props();
</script>

<label class="flex flex-col gap-1.5">
	<span class="text-sm text-ink-muted">{label}</span>
	{@render children()}
</label>
