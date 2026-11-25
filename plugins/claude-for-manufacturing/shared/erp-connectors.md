# The ERP connector: Oracle NetSuite or Infor M3

**Shared across the plugin.** Wherever a skill says *the ERP*, it means
whichever of these two is live for the plant: **Oracle NetSuite** or **Infor
M3**. A plant runs one. The profile's `### Systems` line names it
(`../skills/onboarding/reference/config-profile.md`).

NetSuite is the worked example throughout the skills, because it was the first.
This file is where M3 differs. Read it before any M3 pull.

---

## Which one is live

**A connector is live only when its tools exist in this session and return.**

- **NetSuite:** the NetSuite connector's tools.
- **Infor M3:** tools named `M3_<program>_<transaction>`, for example
  `M3_MNS150MI_GetUserData_CurrentUser`. The server's own name differs per
  company; the `M3_` tool names do not. The connection test is
  `MNS150MI_GetUserData_CurrentUser`: it returns the signed-in user's
  `Company`, `Division`, `Facility` and `Warehouse`, and pulls no business data.

Infor CloudSuite Industrial and Infor LN are different products. They are not
this connector and stay in the `custom-connector` registry.

---

## Record by record

The only M3 calls a skill may make are the ones in this table.

| What the plugin reads | NetSuite | Infor M3 call | M3 fields used |
|---|---|---|---|
| Part master | `item`, `assemblyitem` | `MMS200MI_SearchItem`, `MMS200MI_GetItmBasic` | `ItemNumber`, `ItemName`, `Status`, `BasicUnitOfMeasure`, `MakeBuyCode`, `ItemGroup` |
| Item at a warehouse | `item` by location | `MMS200MI_GetItmWhsBasic`, `MMS200MI_GetItmWhsBal` | `Warehouse`, `Location`, `Buyer` |
| On hand by location and lot | `inventorynumber`, `location` | `MMS060MI_List` | `Location`, `BatchNumber` (the lot), `BalanceIdStatus`, `ApprovedOnHandBalance`, `AllocatedQuantityBasicUom` |
| Production work orders | `workorder` | `PMS100MI_SearchMO`, `PMS100MI_Get` | `ManufacturingOrderNumber`, `ProductNumber`, `WorkOrderStatus`, `OrderedQuantity`, `ManufacturedQuantity`, `StartDate`, `PlannedFinishDate`, `Facility` |
| Operation standards and actuals | closed work orders | `PMS100MI_LstOperations` | `OperationNumber`, `WorkCenter`, `SetupTime`, `RunTime`, `UsedLaborSetupTime`, `UsedLaborRunTime`, `CompletedQuantity`, `ScrappedQuantity`, `ReportingDate` |
| Materials on a work order | work order components | `PMS100MI_LstMaterials` | component item and quantities, as returned |
| Sales orders | `salesorder` | `OIS100MI_SearchHead_LimitedOutput` | `OrderNumber`, `CustomerNumber`, `OrderDate`, `RequestedDeliveryDateAtDestination`, `HighestOrderStatus`, `LowestOrderStatus` |
| Shipped lines | `itemfulfillment` | `MWS411MI_LstDelLnByOrd`, `DRS100MI_LstShipment` | `DeliveryNumber`, `OrderNumber`, `OrderLineNumber`, `ItemNumber`, `TransactionQuantity`; shipment `DepartureDate`, `HighestShipmentStatus` |
| Purchase orders | `purchaseorder` | `PPS200MI_SearchHead`, `PPS200MI_LstLine` | `PurchaseOrderNumber`, `SupplierNumber`, `ItemNumber`, `PurchasePrice`, `OrderedQuantity`, `ReceivedQuantity`, `RejectedQuantity`, `ReceiptDate` |
| Receipts | `itemreceipt` | `PPS200MI_LstReceiptsByPO` | `ReceivingNumber`, `TransactionDate`, `ReportedQuantity` |
| Suppliers | `vendor` | `CRS620MI_SearchSupplier`, `PPS115MI_LstAltSupplier` | `SupplierNumber`, `SupplierName`, `Status`, `Country` |
| Usage and open demand | usage history | `MMS080MI_LstMtPlByItmWhs` | `PlanningDate`, `TransactionQuantity`, `OrderCategory`, `OrderNumber` |
| Server clock | account time zone | `ARS200MI_ServerTimeZone` | `UTCTime` |

**Scope.** NetSuite scopes by subsidiary and location; M3 scopes by
**facility and warehouse**. Company and division come from the signed-in user.
Every M3 pull is filtered by the facility and warehouses in the profile's
`### ERP scope` and by the date window. Never an unfiltered search.

---

## What M3 does not give, and what the skill does instead

Each of these takes the fallback the skill already has for that one input when
the ERP is not connected. Say which input fell back and why, in the output.
Every other ERP input still comes from M3.

| Not available from M3 | Why | Fallback |
|---|---|---|
| Standard cost | `MMS200MI_GetItmPrice` is not called | Last purchase price from `PPS200MI_LstLine`, then an export or a supplied cost, labelled with its source. Never zero |
| Quote history | `OIS100MI_SearchQuotation` is not called | Prior quotes from documents only |
| Customer order lines by search | `OIS100MI_SearchLine_LimitedOutput` is not called | Lines come from delivery lines (`MWS411MI_LstDelLnByOrd`) and the material plan |
| Lot on a shipment or a receipt | Not in either call's output | On-hand lots and lots on work orders are read; what shipped or came in by lot is **unverified** until confirmed |
| Part revision | Not on the item record | Where the profile's `### ERP scope` says it lives: item-ID suffix, or the drawing |
| Routings and BOMs | Not exposed by the M3 server | The routing or BOM export, as for a NetSuite account without routings licensed |
| Customer contacts, supplier contacts | Not in the search output | Documents, or asked for |

The skills do not call `MMS200MI_GetItmPrice`, `OIS100MI_SearchQuotation` or
`OIS100MI_SearchLine_LimitedOutput`. If an Infor M3 tool call returns an
error, tell the user and fall back to a file export.

---

## Reading M3 output

1. **Empty comes back as an error.** "Record does not exist" from a list call
   means *none found*. Report it as empty, never as a failed check and never as
   zero (`absent-is-not-zero.md`). Any other error is a failed check, reported
   with the call that failed.
2. **Two date formats, sometimes in one record.** `YYYYMMDD` (`20261015`) and
   `YYYY-MM-DD` (`2026-10-15`) both occur; shipments carry one of each. Read
   both. A time like `1600` is 16:00.
3. **Status codes come back as numbers or names.** A purchase order searched
   with `Put-away` can return `"75"`. Key status logic on the code:
   order lines `66` delivered, `77` invoiced, `90` deleted; purchase orders
   `75` put away, `85` invoiced; work orders by `WorkOrderStatus` name
   (`OrderCompleted`, `OrderReady` are closed). Deleted records (`90`) are out
   of every count.
4. **Searches stop at about 30 rows and say nothing.** When a call returns 30
   or more rows, assume more exist: narrow the filter (by date, item, status)
   and pull again until a page returns fewer. Say in the data quality report
   when a source was pulled in slices.
5. **`RunTimeHours` is not hours.** Use `SetupTime`, `RunTime`,
   `UsedLaborSetupTime` and `UsedLaborRunTime`, in the time unit the profile's
   `### ERP scope` records for M3, and never `RunTimeHours`. M3 sets the unit
   per work center, so it is asked at onboarding, never assumed. Until it is
   recorded, operation times are reported as read, unit unconfirmed, and are
   not costed.
6. **Quantities are positive.** M3 writes order, delivery and receipt
   quantities positive. NetSuite writes sales order and fulfilment lines
   negative. Only the material plan signs demand negative. Record the M3 sign
   rule per record type in `join-keys.md`'s *Integrity checks*.
7. **Inspection status is on the balance.** `BalanceIdStatus` `1` is under
   inspection, `2` approved, `3` rejected. Stock under inspection is not
   available stock, and NCR containment reads it as already held.

**Source tags.** Rows from M3 carry `source_system` `infor_m3`, and a
reference is `infor_m3:<record>/<id>`, such as `infor_m3:mo/4001015937` or
`infor_m3:delivery/4111327`.

---

## Never written to

The same write guard as NetSuite (`approval-gates.md`). **No skill calls any M3
transaction outside the table above**, approval or not. The M3 server exposes
writes that can add, change and delete customer orders, create, hold, split,
reschedule and delete work orders, approve and change purchase orders, change
item prices, confirm pick lists and release orders. None of them is ever
called. A request to do one ("release MO 4001015937") gets a draft of the
change for a person to make in M3, and says nothing was changed.
