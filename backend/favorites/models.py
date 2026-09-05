# backend/favorites/models.py

# legacy `Favorite` model は `favorites.0003_retire_legacy_favorite` で退役済み。
# favorite の live 正本は `temples.models.Favorite`（table `temples_favorite`）。
#
# この app は Stage 1 時点では INSTALLED_APPS に残しており（`favorites.permissions` に
# test consumer があるため）、model を持たない状態で維持する。
