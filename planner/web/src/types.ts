export type SaveSlot = {
  slot_id: string;
  label: string;
  mtime: number;
  latest_file: string;
};

export type Language = { name: string; code: string };

export type Today = {
  date: string;
  season: string;
  year: number;
  week_in_season: number;
  day_of_week: string;
  next_trend_rotation_in_days: number;
  money_copper: number;
  money_silver: number;
  tavern_rep: number;
  planted_count: number;
  unique_planted: number;
  unlocked_recipes: number;
};

export type TrendItem = {
  item_id: number;
  name: string;
  is_food: boolean;
  contains_alcohol: boolean;
  grow_crop_id: number | null;
  grow_crop_name: string | null;
  grow_in_season_now: boolean;
  grow_best_season_now: boolean;
  is_planted: boolean;
  planted_count: number;
  recipe_ids: number[];
  unlocked_recipe_ids: number[];
};

export type CookSuggestion = {
  recipe_id: number;
  recipe_name: string;
  output_item_id: number;
  output_name: string;
  profit_per_craft: number;
  profit_per_hour: number;
  base_profit_with_trend: number;
  time_hours: number;
  fuel: number;
  ingredients: [number, number, string][];
  missing_ingredients: string[];
  why: string[];
};

export type PlantSuggestion = {
  crop_id: number;
  crop_name: string;
  days_to_grow: number;
  reusable: boolean;
  days_until_new_harvest: number;
  available_seasons: string[];
  best_seasons: string[];
  is_best_now: boolean;
  yield_per_harvest: number;
  target_for_trend_week: number;
  plant_by_day: number;
  why: string[];
};

export type WeekPlan = {
  week_offset: number;
  days_until_start: number;
  season_at_start: string;
  food_trends: TrendItem[];
  drink_trends: TrendItem[];
  ingredient_trends: TrendItem[];
};

export type Plan = {
  state: { slot_id: string; save_path: string; save_mtime: number };
  today: Today;
  cook_now: CookSuggestion[];
  brew_now: CookSuggestion[];
  plant_now: PlantSuggestion[];
  calendar: WeekPlan[];
  money_silver: number;
};
