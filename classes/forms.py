from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class PreapproveStudentsForm(forms.Form):
    """
    Formulário para adicionar emails de alunos a serem pré-aprovados para uma turma.
    Permite colar uma lista de emails ou carregar um ficheiro.
    """
    email_list = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'placeholder': 'Cole os emails aqui, um por linha...'}),
        required=False,
        label="Lista de Emails",
        help_text="Cole uma lista de emails, um por linha."
    )
    
    email_file = forms.FileField(
        required=False,
        label="Ou Carregue um Ficheiro",
        help_text="Carregue um ficheiro (.txt ou .csv) com um email por linha ou emails separados por vírgula."
    )

    def clean(self):
        """
        Validação extra:
        - Garante que pelo menos um dos campos (lista ou ficheiro) foi preenchido.
        - Extrai e valida emails de ambos os campos.
        - Retorna uma lista limpa de emails únicos e válidos.
        """
        cleaned_data = super().clean()
        email_list_str = cleaned_data.get('email_list')
        email_file = cleaned_data.get('email_file')
        
        if not email_list_str and not email_file:
            raise ValidationError("Por favor, forneça uma lista de emails na caixa de texto ou carregue um ficheiro.")
            
        emails = set() # Usar um set para evitar duplicados iniciais
        invalid_emails = []
        
        # Processar caixa de texto
        if email_list_str:
            lines = email_list_str.strip().splitlines()
            for line in lines:
                email = line.strip()
                if not email:
                    continue
                try:
                    validate_email(email)
                    emails.add(email.lower()) # Normalizar para minúsculas
                except ValidationError:
                    invalid_emails.append(email)
                    
        # Processar ficheiro
        if email_file:
            try:
                # Tentar ler como texto, assumindo UTF-8
                content = email_file.read().decode('utf-8').strip()
                # Dividir por novas linhas ou vírgulas
                potential_emails = []
                if ',' in content:
                    potential_emails = [e.strip() for e in content.split(',')]
                else:
                    potential_emails = [e.strip() for e in content.splitlines()]
                
                for email in potential_emails:
                    if not email:
                        continue
                    try:
                        validate_email(email)
                        emails.add(email.lower()) # Normalizar para minúsculas
                    except ValidationError:
                        invalid_emails.append(email)
                        
            except UnicodeDecodeError:
                raise ValidationError("Não foi possível ler o ficheiro. Certifique-se que está codificado em UTF-8.")
            except Exception as e:
                 raise ValidationError(f"Erro ao processar o ficheiro: {e}")

        if invalid_emails:
            # Anexa a lista de emails inválidos ao erro do campo email_list ou email_file
            # Ou podemos levantar um erro não relacionado a campo
             raise ValidationError(f"Os seguintes emails são inválidos ou não foram processados: {', '.join(invalid_emails)}")

        if not emails:
            raise ValidationError("Nenhum email válido foi encontrado na lista ou no ficheiro.")

        # Adicionar a lista limpa aos dados limpos para uso na view
        cleaned_data['valid_emails'] = list(emails)
        
        return cleaned_data 