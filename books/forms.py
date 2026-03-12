from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["review"]


class AddToCartForm(forms.Form):
    book_id = forms.UUIDField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm", "style": "width:70px"}),
    )


class UpdateCartItemForm(forms.Form):
    book_id = forms.UUIDField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm", "style": "width:70px"}),
    )


class RemoveFromCartForm(forms.Form):
    book_id = forms.UUIDField(widget=forms.HiddenInput)
