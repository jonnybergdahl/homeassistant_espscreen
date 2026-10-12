// clang++ -std=c++17 -Wall -Wextra -Werror -I. tests/test_plant_card.cpp -o /tmp/test_plant_card && /tmp/test_plant_card
#include "../components/smart_display/plant_card.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <vector>

using namespace plant_card;

// A look's sizes, as runtime_tiles measures them: the compact (CYD) and the standard (Guition 4-inch) and a dense glass.
static Input look(int width, int height, int scale, size_t readings, bool species, bool photo = false) {
  Input in;
  in.width = width; in.height = height;
  in.icon_w = in.icon_h = 20 * scale / 100;
  in.line_h = 22 * scale / 100;
  in.species_h = species ? 18 * scale / 100 : 0;
  in.gap = 6 * scale / 100; in.row_gap = 8 * scale / 100; in.column_gap = 16 * scale / 100;
  if (photo) { in.photo_max = 120 * scale / 100; in.photo_min = 64 * scale / 100; }
  // "14.5 %", "21000 lx", "3.1 mol/d⋅m²": the widest of Olen's readings is the light integral with its unit.
  const int widths[] = {60, 84, 70, 90, 60, 120, 70, 66};
  for (size_t i = 0; i < readings; ++i) in.value_w.push_back(widths[i % 8] * scale / 100);
  return in;
}

int main() {
  // Every shape a card can land on: nothing past its room, no two readings on each other, the first readings kept.
  for (int scale : {60, 100, 160})
    for (int width = 150; width <= 1100; width += 37)
      for (int height = 20; height <= 600; height += 23)
        for (size_t n = 0; n <= MAX_READINGS; ++n)
          for (bool species : {false, true})
          for (bool photo : {false, true}) {
            const Input in = look(width, height, scale, n, species, photo);
            const Layout l = place(in);
            assert(l.height <= height);
            // The photo: a square within the room, in the middle, between its smallest and largest, and only with
            // every reading and the species under it.
            if (l.photo) {
              assert(photo && l.photo >= in.photo_min && l.photo <= in.photo_max && l.photo <= width);
              assert(l.photo_x >= 0 && l.photo_x + l.photo <= width && std::abs(2 * l.photo_x + l.photo - width) <= 1);
              assert(l.cells.size() == n && l.species == species);
              for (const Cell &c : l.cells) assert(c.y >= l.photo);
            }
            assert(l.cells.size() <= n);
            assert(l.columns >= 1 && l.columns <= 2);
            if (l.species) assert(species && l.cells.size() == n);
            for (size_t i = 0; i < l.cells.size(); ++i) {
              const Cell &c = l.cells[i];
              assert(c.x >= 0 && c.y >= 0 && c.x + c.w <= width && c.y + c.h <= height);
              assert(c.h == l.row_h && c.w > 0);
              for (size_t j = 0; j < i; ++j) {
                const Cell &o = l.cells[j];
                assert(c.x >= o.x + o.w || o.x >= c.x + c.w || c.y >= o.y + o.h || o.y >= c.y + c.h);
              }
              // Reading order: across a row, then down, as the flower card fills its rows.
              if (i) assert(c.y > l.cells[i - 1].y || c.x > l.cells[i - 1].x);
            }
          }
  // Two to a row on a card that is wide enough, as the flower card: six readings in three rows, species on top.
  {
    const Layout l = place(look(440, 300, 100, 6, true));
    assert(l.columns == 2 && l.cells.size() == 6 && l.species);
    assert(l.cells[1].y == l.cells[0].y && l.cells[2].y > l.cells[0].y && l.cells[0].y > 0);
    // The left column stands against the middle, the right one starts from it.
    assert(l.cells[0].end && !l.cells[1].end && l.cells[2].end && !l.cells[3].end);
  }
  // A card too narrow for two of its widest values side by side: one to a row.
  {
    const Layout l = place(look(130, 400, 60, 5, false));
    assert(l.columns == 1 && l.cells.size() == 5);
    for (const Cell &c : l.cells) assert(!c.end);
  }
  // A short card gives up the species before any reading.
  {
    Input in = look(440, 0, 100, 6, true);
    in.height = 3 * 22 + 2 * 8;
    const Layout l = place(in);
    assert(!l.species && l.cells.size() == 6 && l.cells[0].y == 0);
  }
  // Shorter still: the readings that have no row left go, the last ones first.
  {
    Input in = look(440, 0, 100, 6, false);
    in.height = 2 * 22 + 8;
    const Layout l = place(in);
    assert(l.cells.size() == 4);
  }
  // A photo where there is room, above the species and the readings, as the flower card's header has it.
  {
    const Layout l = place(look(440, 400, 100, 6, true, true));
    assert(l.photo == 120 && l.species && l.species_y == 128 && l.cells.size() == 6 && l.cells[0].y > l.species_y);
  }
  // A shorter card shrinks the photo, then drops it before the species or a reading.
  {
    Input in = look(440, 0, 100, 6, true, true);
    const int rest = 18 + 8 + 3 * 22 + 2 * 8;
    in.height = rest + 8 + 80;
    assert(place(in).photo == 80);
    in.height = rest + 8 + 40;
    const Layout l = place(in);
    assert(l.photo == 0 && l.species && l.cells.size() == 6);
  }
  // A plant without readings yet shows its species alone.
  {
    const Layout l = place(look(300, 200, 100, 0, true));
    assert(l.species && l.cells.empty() && l.height == 18);
  }
  // Too low or too high is a problem; no word from the plant is none.
  assert(problem(Reading{0, "12", "%", 'l'}) && problem(Reading{0, "3400", "µS/cm", 'h'}) && !problem(Reading{}));
  std::puts("plant card: ok");
}
