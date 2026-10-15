// Pure group-delivery decisions, factored out of server.ts so they can be unit-tested without
// opening chat.db or starting the MCP server. No I/O, no side effects — every input is passed in.

// What to do with an is_from_me row in the inbound pump. Self-chat handles its own echoes
// elsewhere; this is the group case. The caller only consumes the echo window (a side effect)
// once it knows the group has opted in, so `isRecentEcho` is passed in already resolved.
//
//   drop              - not opted in, or this is the assistant's OWN send (a recent echo)
//   deliver-as-owner  - the owner typed this directly in an opted-in group
export function fromMeGroupAction(
  isGroup: boolean,
  deliverOwnGroupMessages: boolean,
  isRecentEcho: boolean,
): 'drop' | 'deliver-as-owner' {
  if (!isGroup) return 'drop'
  if (!deliverOwnGroupMessages) return 'drop'
  if (isRecentEcho) return 'drop'
  return 'deliver-as-owner'
}

// Whether the per-group member allowlist admits this sender. An empty allowlist admits anyone
// (subject to requireMention, applied by the caller). The owner (fromMe) is always admitted —
// the allowlist restricts other people, not the account owner.
export function passesGroupAllowFrom(
  groupAllowFrom: string[],
  senderId: string,
  fromMe: boolean,
): boolean {
  if (fromMe) return true
  if (groupAllowFrom.length === 0) return true
  return groupAllowFrom.includes(senderId)
}
