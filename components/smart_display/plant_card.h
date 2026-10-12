#pragma once
// The plant card (firmware 0.56.0+): what a tap on a plant's tile opens. Under the card's status line (Home Assistant's
// OK or Problem) it shows the species and each reading with its icon and its value, the value red while the plant says
// it is too low or too high, as Home Assistant's plant-status card shows them (hui-plant-status-card.ts), two to a row
// as the flower card puts them (Olen's lovelace-flower-card, bars_per_row). Home Assistant's own plant and Olen's
// replacement reach the screen in the same form: the add-on gathers the readings of both (core.plant_extras).
//
// The plant's own block of extras, so no other tile's extras grow by it, and where everything goes. Pure, free of LVGL
// and ESPHome: tests/test_plant_card.cpp checks every shape on a PC; runtime_tiles.h measures the texts and draws.
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace plant_card {
// One reading: its icon (a Material Design codepoint, 0 for none the font has), its value as Home Assistant shows it
// (empty while it has none), its unit, and `l` or `h` while the plant reports it too low or too high.
struct Reading {
  uint32_t icon = 0;
  std::string value, unit;
  char status = 0;
};
constexpr size_t MAX_READINGS = 8;
struct Data {
  std::vector<Reading> readings;
  std::string species;
};
inline bool problem(const Reading &r) { return r.status == 'l' || r.status == 'h'; }

// What the card has to work with, in pixels: the room under its status line, an icon, a line of the value's font and of
// the species' (0 without a species), the gaps, each reading's value with its unit as the font measures it, and the
// plant's photo: the largest and the smallest square worth drawing (0 without a photo, or on a board without pictures).
struct Input {
  int width = 0, height = 0;
  int icon_w = 0, icon_h = 0, line_h = 0, species_h = 0;
  int photo_max = 0, photo_min = 0;
  int gap = 0, row_gap = 0, column_gap = 0;
  std::vector<int> value_w;
  int max_columns = 2;
};
// `end`: the cell's icon and value stand against its right edge. Two to a row, the left column's do, so each pair stands
// against the middle of the card and the two columns read as one block around it; one to a row, every pair starts left.
struct Cell { int x = 0, y = 0, w = 0, h = 0; bool end = false; };
// Where each reading stands (the first `cells.size()` of them), the photo (a square of `photo` pixels at the top, in the
// middle; 0 for none), the species line, and the height it all takes.
struct Layout {
  bool species = false;
  int photo = 0, photo_x = 0;
  int species_y = 0, columns = 1, row_h = 0, height = 0;
  std::vector<Cell> cells;
};

// Two to a row where both of the widest fit beside each other, else one. What gives when the glass is short, in this
// order: the photo (it shrinks to its smallest, then goes: it shows the plant, the readings say how it is), the species
// (a word about the plant), then the readings that no row is left for, the last ones first: the flower card's order puts
// what a plant needs most (its soil moisture) first. Nothing is ever placed past the room.
inline Layout place(const Input &in) {
  Layout out;
  const size_t n = in.value_w.size();
  out.row_h = std::max(in.icon_h, in.line_h);
  if (in.width <= 0 || in.height <= 0 || out.row_h <= 0) return out;
  const int widest = n ? *std::max_element(in.value_w.begin(), in.value_w.end()) : 0;
  const int need = in.icon_w + in.gap + widest;
  int columns = std::max(1, std::min(in.max_columns, static_cast<int>(n)));
  while (columns > 1 && columns * need + (columns - 1) * in.column_gap > in.width) --columns;
  out.columns = columns;
  const int cell_w = (in.width - (columns - 1) * in.column_gap) / columns;
  const int rows = static_cast<int>((n + columns - 1) / columns);
  auto stack = [&](int count, bool species) {
    const int lines = count > 0 ? count * out.row_h + (count - 1) * in.row_gap : 0;
    return (species ? in.species_h + (count > 0 ? in.row_gap : 0) : 0) + lines;
  };
  // The photo takes what the species and every reading leave, up to its largest, and stands only when that is at least
  // its smallest.
  if (in.photo_max > 0) {
    const int rest = in.species_h > 0 || rows > 0 ? stack(rows, in.species_h > 0) + in.row_gap : 0;
    const int photo = std::min({in.photo_max, in.width, in.height - rest});
    if (photo >= std::max(1, in.photo_min)) { out.photo = photo; out.photo_x = (in.width - photo) / 2; }
  }
  const int below = out.photo ? out.photo + in.row_gap : 0, height = in.height - below;
  out.species = in.species_h > 0 && in.species_h <= height && stack(rows, true) <= height;
  int fit = rows;
  const int room = height - (out.species ? in.species_h + in.row_gap : 0);
  while (fit > 0 && stack(fit, false) > room) --fit;
  const size_t shown = std::min(n, static_cast<size_t>(fit) * columns);
  out.species_y = below;
  const int top = below + (out.species ? in.species_h + in.row_gap : 0);
  for (size_t i = 0; i < shown; ++i) {
    const int row = static_cast<int>(i) / columns, column = static_cast<int>(i) % columns;
    out.cells.push_back({column * (cell_w + in.column_gap), top + row * (out.row_h + in.row_gap), cell_w, out.row_h,
                         columns == 2 && column == 0});
  }
  out.height = shown ? out.cells.back().y + out.row_h : out.species ? below + in.species_h : out.photo;
  return out;
}
}  // namespace plant_card
