// hu: A Telegram-nyugtazast (pl. emoji-reakcio) a Claude fele valo kezbesites
// SIKEREHEZ koti. Az `ack` callback csak azutan fut le, hogy a `deliver`
// tenylegesen lefutott -- enelkul egy MCP-kiesesi ablakban a feladó
// "kezbesitve" jelzest kapna egy olyan uzenetre, ami sosem jutott el Claude-hoz.
//
// en: Ties the Telegram acknowledgment (e.g. an emoji reaction) to the
// SUCCESS of delivery to Claude. The `ack` callback only runs once `deliver`
// has actually completed -- without this, an MCP outage window would show
// the sender a "delivered" signal for a message that never reached Claude.
export async function deliverAndAck(
  deliver: () => Promise<unknown>,
  ack: () => void,
  onFailure: (err: unknown) => void,
): Promise<boolean> {
  try {
    await deliver()
  } catch (err) {
    onFailure(err)
    return false
  }
  ack()
  return true
}
