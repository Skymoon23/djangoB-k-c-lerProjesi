from django import forms
from .models import EvaluationComponent, LearningOutcome


class EvaluationComponentForm(forms.ModelForm):
    class Meta:
        model = EvaluationComponent
        fields = ['name', 'percentage']
        labels = {
            'name': 'Bileşen Adı (Vize, Final, Proje vb.)',
            'percentage': 'Yüzdelik Ağırlığı',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }


class LearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ['description']
        labels = {
            'description': 'Öğrenim Çıktısı Açıklaması',
        }
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
