# Trade-offs: rules that depend on context

| Practice | When it holds / when it doesn't |
|---|---|
| Adopt a vendor's stored-conversation feature | Convenient, but opaque, grows unbounded and locks you in. Default to owned memory with a token cap. |
| One database with tenant_id vs one per tenant | Shared schema suits one team and shared reference data; separate databases suit isolation, compliance or per-client restore. |
| Build an adapter/registry before the second instance | Usually premature; justified only when the second instance is committed. |
| Server-wide statement timeout | Kills migrations and backups; set per role. |
| Tests that pin counts or config text | Brittle; keep only for true invariants and say why. |
| "Files under N lines" | A heuristic; split by responsibility. |
| Mass renames for naming conventions | High churn and migration risk; apply to new code, rename old code when touched. |
| Merge commits vs squash for stacked PRs | Depends on tooling; the deeper fix is shallow stacks. |
| Tightest possible test tolerance | Flaky across platforms; derive from the domain's precision. |
| Range heuristics for units ("≥ 1 is not a fraction") | Works only where values never approach the boundary; prefer explicit units. |
| VACUUM FULL / table rewrites | Take exclusive locks; schedule downtime or use online tools (pg_repack). |
| Compose file secrets without Swarm | Better than env vars, but plain files: permissions and host security still matter. |
| Copying a legacy tool's quirks | Right when users live in that tool; otherwise can surprise new users. |
