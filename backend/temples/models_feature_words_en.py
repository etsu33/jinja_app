# backend/temples/models_feature_words_en.py
"""神社ごとの英語の特徴語（travel モードの検証用）。

1行 = 1つの神社 × 1つの特徴語 × 1つの根拠。
同じ語に根拠が2つあれば2行になる（例：日光東照宮の C_CARVINGS）。

- 正本は Google スプレッドシート「KAMI MUSUBI 英語版の特徴語と10社の当てはめ表」。
  リポジトリの temples/data/feature_words_en/*.json はその写しで、
  import_feature_words_en コマンドがこの表に取り込む。
- 語の一覧は temples/domain/feature_words_en.py の FEATURE_WORDS。
- 今は記録用で、並び順には使っていない。
"""

from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint


class ShrineFeatureWordEn(models.Model):
    shrine = models.ForeignKey(
        "temples.Shrine",
        on_delete=models.CASCADE,
        related_name="feature_words_en",
    )
    word_id = models.CharField(
        max_length=64,
        help_text="FEATURE_WORDS の ID（例: S_FOREST）",
    )
    vocabulary_version = models.CharField(
        max_length=16,
        help_text="語彙のバージョン（例: 2026-11-12）",
    )
    evidence_quote = models.TextField(help_text="公式の文言の引用")
    note = models.TextField(blank=True, default="", help_text="備考")
    source_url = models.URLField(max_length=500, help_text="出典URL")
    source_type = models.CharField(max_length=32, help_text="出典の種類（例: 神社公式）")
    checked_on = models.DateField(help_text="確認日")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "temples_shrine_feature_word_en"
        ordering = ["shrine_id", "id"]
        constraints = [
            CheckConstraint(condition=~Q(word_id=""), name="chk_feature_word_en_word_id_nonempty"),
            CheckConstraint(
                condition=~Q(evidence_quote=""),
                name="chk_feature_word_en_quote_nonempty",
            ),
            UniqueConstraint(
                fields=["shrine", "word_id", "source_url", "evidence_quote"],
                name="uniq_feature_word_en_evidence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.shrine_id}:{self.word_id}"
