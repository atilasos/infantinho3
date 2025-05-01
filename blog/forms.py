# blog/forms.py
from django import forms
from .models import Post, Comment, Class
from django.utils.translation import gettext_lazy as _
# Import the standard widget since django-ckeditor-uploader is not installed
# from ckeditor.widgets import CKEditorWidget # REMOVED
from tinymce.widgets import TinyMCE # ADDED

class PostForm(forms.ModelForm):
    """
    Form for creating and editing blog Posts.
    Includes class selection.
    """
    # Add class selection field
    turma = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('name'), 
        label=_("Class"),
        help_text=_("Select the class this post relates to, or leave blank for a general announcement."),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- Geral (Toda a Escola) ---")
    )
    
    class Meta:
        model = Post
        # REMOVED 'subcategoria_diario' from fields
        fields = ['turma', 'titulo', 'categoria', 'conteudo', 'image', 'attachment']
        widgets = {
            # 'conteudo': CKEditorWidget(), # REPLACED
            'conteudo': TinyMCE(), # with TinyMCE
        }
        labels = {
            'turma': _("Class"), # Explicitly add label here now
            'titulo': _('Title'),
            'conteudo': _('Content'),
            'categoria': _('Category'),
            # Removed subcategoria label
            'image': _('Image'),
            'attachment': _('Attachment (PDF, etc.)'),
        }
        help_texts = {
            'titulo': _('(Optional)'),
            # Removed subcategoria help_text
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization to set widget choices and requirements.
        """
        super().__init__(*args, **kwargs)
        # Customize category widget
        self.fields['categoria'].widget = forms.Select(choices=Post.CATEGORIA_CHOICES)
        self.fields['categoria'].widget.attrs.update({'class': 'form-select'})
        
        # REMOVED subcategoria customizations
        # self.fields['subcategoria_diario'].widget = ...
        # self.fields['subcategoria_diario'].required = False 

        self.fields['image'].required = False 
        self.fields['attachment'].required = False 

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
