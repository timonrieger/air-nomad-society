<script lang="ts">
	let { label }: { label: string } = $props();
</script>

<div class="my-16 flex flex-col items-center gap-4" role="status">
	<div
		class="size-10 animate-spin rounded-full border-[3px] border-line border-t-accent border-r-accent/30 motion-reduce:animate-[spin_1.5s_linear_infinite]"
	></div>
	<p class="text-ink-muted">{label}</p>
</div>
