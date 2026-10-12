// A plant on the mockup (firmware 0.56.0+), as the screen draws it: active and Home Assistant's red only while it has a
// problem (state_active.ts, --state-plant-active-color), listed under a filter of its own.
import { describe, expect, it } from "vitest";
import { t } from "../src/i18n";
import { FILTERS, entryTone } from "../src/model/library";
import { domains } from "../src/model/layout";
import { accent, tileActive } from "../src/model/tile-palette";

describe("a plant", () => {
  it("is coloured only while it has a problem, in Home Assistant's red", () => {
    expect(tileActive("plant.fern", { state: "problem", a: {} })).toBe(true);
    expect(tileActive("plant.fern", { state: "ok", a: {} })).toBe(false);
    expect(accent("plant.fern", { state: "problem", a: {} })).toBe(accent("binary_sensor.smoke", { state: "on", a: { device_class: "smoke" } }));
    expect([entryTone({ id: "plant.fern", state: "problem" }), entryTone({ id: "plant.fern", state: "ok" })]).toEqual(["on", ""]);
  });

  it("has a filter and a name in the library", () => {
    expect(FILTERS).toContain("plant");
    expect(t("editor.library.filters.plant")).toBe("Plants");
    expect(t("editor.domains.plant")).toBe("Plant");
    expect(domains.plant[0]).toBe("✿");
  });
});
