const p01 = require("./plugins/coe-pricing/prompts/01-vin-intelligence.js");
const p02 = require("./plugins/coe-pricing/prompts/02-moi-accident.js");
const p03 = require("./plugins/coe-pricing/prompts/03-price-normalization.js");
const p04 = require("./plugins/coe-pricing/prompts/04-auction-intelligence.js");
const p05 = require("./plugins/coe-pricing/prompts/05-gcc-nongcc-verification.js");
const p06 = require("./plugins/coe-pricing/prompts/06-executive-summary.js");
const p07 = require("./plugins/coe-pricing/prompts/07-master-full-scan.js");
const p08 = require("./plugins/coe-pricing/prompts/08-reliability-residual.js");
const p09 = require("./plugins/coe-pricing/prompts/09-copilot-handoff.js");
const cfg = require("./plugins/coe-pricing/config/workflow.config.js");
const AfSvc  = require("./plugins/coe-pricing/services/af-pricing-agent.js");
const DubSvc = require("./plugins/coe-pricing/services/dubizzle-scraper.js");
const CopSvc = require("./plugins/coe-pricing/services/copilot-handoff.js");

const af  = new AfSvc(cfg.services.afPricingAgent);
const dub = new DubSvc(cfg.services.vehiclePricingWidget);
const cop = new CopSvc();

const CMD = {
  "vin-scan":          function(p) { return p01.run(p); },
  "moi-accident":      function(p) { return p02.run(p); },
  "price-engine":      function(p) { return p03.run(p, dub); },
  "auction-intel":     function(p) { return p04.run(p); },
  "gcc-verify":        function(p) { return p05.run(p); },
  "exec-summary":      function(p) { return p06.run(p, af); },
  "master-scan":       function(p) { return p07.run(p, {afPricingAgent:af,dubizzleScraper:dub,copilotHandoffSvc:cop}); },
  "reliability-score": function(p) { return p08.run(p); },
  "copilot-handoff":   function(p) { return p09.run(p, cop); },
};

function parseArgs(argv) {
  var args = argv.slice(2);
  var command = args[0];
  var params = {};
  for (var i = 1; i < args.length; i++) {
    if (args[i].indexOf("--") === 0) {
      var key = args[i].slice(2);
      var val = (args[i+1] && args[i+1].indexOf("--") !== 0) ? args[++i] : true;
      params[key] = (isNaN(val) || val === true) ? val : Number(val);
    }
  }
  return { command: command, params: params };
}

var D = "=".repeat(66);
var d = "-".repeat(66);

function print(r) {
  console.log("\n" + D);
  if (r.vehicle) console.log("  Vehicle : " + r.vehicle);
  if (r.vin)     console.log("  VIN     : " + r.vin);
  if (r.command) console.log("  Command : " + r.command);
  console.log(D + "\n");
  if (r.error) { console.error("Error: " + r.error); return; }
  if (r.masterPrompt)   { console.log(d + "\nMASTER PROMPT - paste into Claude\n" + d); console.log(r.masterPrompt); }
  if (r.prompt)         { console.log(d + "\nPROMPT - paste into Claude\n" + d); console.log(r.prompt); }
  if (r.copilotHandoff) { console.log("\n" + d + "\nCOPILOT HANDOFF - paste into Copilot\n" + d); console.log(r.copilotHandoff); }
  if (r.handoff)        { console.log("\n" + d + "\nHANDOFF\n" + d); console.log(r.handoff); }
  if (r.instructions) { var arr = Array.isArray(r.instructions) ? r.instructions : [r.instructions]; if (arr.length) { console.log("\n" + d + "\nNEXT STEPS\n" + d); arr.forEach(function(s){console.log("  "+s);}); } }
  console.log("\n" + D + "\n");
}

async function main() {
  var parsed = parseArgs(process.argv);
  var command = parsed.command;
  var params  = parsed.params;

  if (command === undefined || command === "help") {
    console.log("\nCOE Pricing Intelligence\n" + d);
    console.log("  node coe-cli.cjs appraise --vin <VIN> --make <MAKE> --model <MODEL> --year <YEAR>");
    console.log("  node coe-cli.cjs <cmd> --vin <VIN> [--make] [--model] [--year]\n");
    console.log("Commands: vin-scan, moi-accident, price-engine, auction-intel,");
    console.log("  gcc-verify, exec-summary, master-scan, reliability-score, copilot-handoff\n");
    return;
  }

  if (command === "appraise") {
    if (params.vin === undefined) { console.error("--vin required"); process.exit(1); }
    var results = await Promise.all([CMD["master-scan"](params), CMD["copilot-handoff"](params)]);
    var ms = results[0]; var hf = results[1];
    print({ command:"appraise", vin:params.vin, vehicle:[params.year,params.make,params.model].filter(Boolean).join(" "), masterPrompt:ms.masterPrompt, copilotHandoff:hf.handoffBlock, instructions:hf.instructions||[] });
    return;
  }

  var fn = CMD[command];
  if (fn === undefined) { console.error("Unknown: " + command); process.exit(1); }
  print(await fn(params));
}

main().catch(function(e){ console.error("Fatal:", e.message); process.exit(1); });