"""PostgreSQL composite FKs retained in model and migration state.

Keep this import path for historical migrations. Existing single-column FKs
continue to own ORM relations and on_delete behavior.
"""

from django.core.exceptions import ValidationError
from django.db import NotSupportedError, models


class CompositeForeignKey(models.BaseConstraint):
    def __init__(self, *, fields, to_model, to_fields, **kwargs):
        self.fields = tuple(fields)
        self.to_model = to_model
        self.to_fields = tuple(to_fields)
        if not self.fields or len(self.fields) != len(self.to_fields):
            raise ValueError("Composite FK columns must be nonempty and have matching lengths")
        super().__init__(**kwargs)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs.update(fields=self.fields, to_model=self.to_model, to_fields=self.to_fields)
        return path, args, kwargs

    def __eq__(self, other):
        return isinstance(other, CompositeForeignKey) and self.deconstruct() == other.deconstruct()

    def constraint_sql(self, model, schema_editor):
        if schema_editor.connection.vendor != "postgresql":
            raise NotSupportedError("Highlights composite foreign keys require PostgreSQL")
        target = model._meta.apps.get_model(self.to_model)
        quote = schema_editor.quote_name
        columns = ", ".join(quote(model._meta.get_field(f).column) for f in self.fields)
        referenced = ", ".join(quote(target._meta.get_field(f).column) for f in self.to_fields)
        return (
            f"CONSTRAINT {quote(self.name)} FOREIGN KEY ({columns}) "
            f"REFERENCES {quote(target._meta.db_table)} ({referenced}) "
            "ON DELETE NO ACTION ON UPDATE NO ACTION NOT DEFERRABLE"
        )

    def create_sql(self, model, schema_editor):
        return f"ALTER TABLE {schema_editor.quote_name(model._meta.db_table)} ADD {self.constraint_sql(model, schema_editor)}"

    def remove_sql(self, model, schema_editor):
        quote = schema_editor.quote_name
        return f"ALTER TABLE {quote(model._meta.db_table)} DROP CONSTRAINT {quote(self.name)}"

    def validate(self, model, instance, exclude=None, using="default"):
        if exclude and set(self.fields).intersection(exclude):
            return
        values = [getattr(instance, model._meta.get_field(f).attname) for f in self.fields]
        if any(value is None for value in values):
            return  # Existing NOT NULL fields validate this separately.
        target = model._meta.apps.get_model(self.to_model)
        query = {
            target._meta.get_field(f).attname: value
            for f, value in zip(self.to_fields, values, strict=True)
        }
        if not target._base_manager.using(using).filter(**query).exists():
            raise ValidationError(
                self.get_violation_error_message(), code=self.violation_error_code
            )
