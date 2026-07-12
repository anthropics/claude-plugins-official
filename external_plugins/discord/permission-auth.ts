/** Permission replies are owner-only, even when a broader group policy admits chat. */
export function isPermissionReplyAuthorized(
  ownerAllowFrom: readonly string[],
  senderId: string,
): boolean {
  return ownerAllowFrom.includes(senderId)
}
