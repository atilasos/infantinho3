from django import forms
from .models import Post, Comment
from ckeditor_uploader.widgets import CKEditorUploadingWidget

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo', 'conteudo', 'categoria', 'subcategoria_diario', 'visibilidade']
        widgets = {
            'conteudo': CKEditorUploadingWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só mostrar subcategoria se categoria for DIARIO
        self.fields['subcategoria_diario'].required = False
        self.fields['subcategoria_diario'].widget = forms.Select(choices=Post.CATEGORIA_DIARIO_CHOICES)
        self.fields['categoria'].widget = forms.Select(choices=Post.CATEGORIA_CHOICES)
        self.fields['visibilidade'].widget = forms.Select(choices=Post.VISIBILIDADE_CHOICES)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['conteudo']
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Escreva um comentário...'}),
        } 