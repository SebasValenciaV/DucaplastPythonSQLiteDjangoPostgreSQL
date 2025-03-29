from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

# Manager custom para Usuarios
class UsuarioManager(BaseUserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Si no se especifica el campo tipo_usuario, se asigna el tipo "Administrador"
        if 'tipo_usuario' not in extra_fields or extra_fields['tipo_usuario'] is None:
            # Se usa apps.get_model para obtener el modelo TipoUsuario
            TipoUsuario = apps.get_model('main', 'TipoUsuario')
            # Se obtiene o crea el registro con id=1, que asumimos es "Administrador"
            extra_fields['tipo_usuario'] = TipoUsuario.objects.get_or_create(
                id=1,
                defaults={'description': 'Administrador'}
            )[0]
        return self._create_user(username, email, password, **extra_fields)

# Modelo para el tipo de usuario
class TipoUsuario(models.Model):
    id = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=25)
    
    def __str__(self):
        return self.description

# Modelo para los estados
class Estados(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=25)

    def __str__(self):
        return self.description

# Modelo para clientes
class Clientes(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, default="")
    dinero_generado = models.BigIntegerField(default=0)
    
    def __str__(self):
        return f"{self.nombre} ID: {self.id}"

# Modelo custom de usuario (login)
class Usuarios(AbstractUser):
    id = models.AutoField(primary_key=True)
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, related_name="customuser_set")
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_set")
    
    # Asignamos nuestro manager custom
    objects = UsuarioManager()
    
    def save(self, *args, **kwargs):
        if not self.password:
            self.set_unusable_password()
        super(Usuarios, self).save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ID: {self.id}"

# Modelo para pedidos
class Pedido(models.Model):
    id = models.AutoField(primary_key=True)
    vendedor = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="vendedor")
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE)
    estado = models.ForeignKey(Estados, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=300)
    fecha = models.DateTimeField(auto_now_add=True)
    valor = models.IntegerField(default=0)
    nota = models.CharField(max_length=500)
    notaDespachador = models.CharField(max_length=500, null=True, blank=True)
    despachado_hora = models.DateTimeField(null=True, blank=True)
    facturado_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True, related_name="facturado_por")
    facturado_hora = models.DateTimeField(null=True, blank=True)
    asignador_reparto = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True, related_name="asignador_reparto")
    asignacion_hora = models.DateTimeField(null=True, blank=True)
    repartido_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True, related_name="repartido_por")
    completado_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True, related_name="completado_por")
    completado_hora = models.DateTimeField(null=True, blank=True)
    
    def get_status_tiempo(self):
        if self.completado_por:
            return 'bg-primary'
        current_time = timezone.now()
        pedido_age = current_time - self.fecha
        if pedido_age < timedelta(hours=1):
            return 'bg-success'
        elif timedelta(hours=1) <= pedido_age <= timedelta(hours=3):
            return 'bg-warning'
        else:
            return 'bg-danger'
    
    def get_status_color(self):
        if self.estado_id == 0:
            return 'bg-danger'
        elif self.estado_id in [1,2]:
            return 'bg-warning'
        elif self.estado_id in [3,4]:
            return 'bg-primary'
        else:
            return 'bg-success'
    
    def actualizar_dinero_generado_cliente(self):
        self.cliente.dinero_generado += self.valor
        self.cliente.save()

# Modelo para productos
class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=400)
    referencia_fabrica = models.CharField(max_length=400)
    precio = models.CharField(max_length=20)
    cantidad = models.IntegerField(default=0)
    
    def __str__(self):
         return self.descripcion

# Modelo intermedio para relacionar productos y pedidos
class ProductosPedido(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)   

# Modelo para el manejo de despacho
class HandlerDespacho(models.Model):
    despachador = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
