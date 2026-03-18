"""
Caso de uso: Crear Entidad Contacto
Descripción: Crea la relación de vinculación entre una entidad y un contacto específico.
Condiciones previas:
    - La entidad debe existir en el sistema.
    - El contacto debe existir en el sistema.
Condiciones posteriores:
    - Se guarda el registro de EntidadContacto en el repositorio.
    - El estado de validación inicial es NO_VALIDADO.
    - Se emiten los eventos EntidadExamplenapshot y EntidadContactoCreado.
"""
