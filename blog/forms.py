# blog/forms.py
from django import forms
from .models import Post, Comment
from django.utils.translation import gettext_lazy as _
# Import the standard widget since django-ckeditor-uploader is not installed
from ckeditor.widgets import CKEditorWidget 

class PostForm(forms.ModelForm):
    """
    Form for creating and editing blog Posts.
    Uses CKEditor for the content field.
    """
    class Meta:
        model = Post
        # Fields displayed in the form
        fields = ['titulo', 'conteudo', 'categoria', 'subcategoria_diario', 'visibilidade']
        # Use CKEditorWidget for the rich text content field
        widgets = {
            # Changed from CKEditorUploadingWidget as the uploader package isn't used
            'conteudo': CKEditorWidget(), 
        }
        labels = {
            'titulo': _('Title'),
            'conteudo': _('Content'),
            'categoria': _('Category'),
            'subcategoria_diario': _('Diary Subcategory'),
            'visibilidade': _('Visibility'),
        }
        help_texts = {
            'titulo': _('(Optional)'),
            # Fixed syntax error: Used double quotes for outer string
            'subcategoria_diario': _("Select only if category is 'Class Diary'."), 
            'visibilidade': _('Currently only Internal visibility is supported.'),
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization to set widget choices and requirements.
        """
        super().__init__(*args, **kwargs)
        # Customize widgets to use dropdowns (Select) for choice fields
        self.fields['categoria'].widget = forms.Select(choices=Post.CATEGORIA_CHOICES)
        # Add a blank choice to subcategory dropdown
        self.fields['subcategoria_diario'].widget = forms.Select(choices=[('', '--------')] + Post.CATEGORIA_DIARIO_CHOICES)
        self.fields['visibilidade'].widget = forms.Select(choices=Post.VISIBILIDADE_CHOICES)
        
        # Ensure subcategory is not required by default 
        # (logic in template might show/hide based on category selection)
        self.fields['subcategoria_diario'].required = False 

    # No clean method needed here as the model's clean method handles 
    # the relationship between categoria and subcategoria_diario on save.

class CommentForm(forms.ModelForm):
    """
    Form for creating blog Comments.
    """
    class Meta:
        model = Comment
        # Only the content field is needed for the form
        fields = ['conteudo']
        widgets = {
            # Use a simple Textarea for comments
            'conteudo': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': _('Write a comment...') # Added translation
            }),
        }
        labels = {
            'conteudo': _('Your Comment'),
        }
