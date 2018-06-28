# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    mrp_bom_modification = fields.Boolean(
        'Modificacion de lista de materiales',
        help='Si la casilla es marcada\nperimite la modificacion de insumos en ordenes de produccion',
    )
