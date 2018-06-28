# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


_ALLOWED_DIFFERENCE = .0000001  # MARGEN PERMITIDO DE DIFERENCIA ENTRE 2 NUMEROS


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.multi
    def compute_product_qty(self):
        if self.bom_id and self.bom_id.product_tmpl_id and self.bom_id.product_tmpl_id.categ_id \
                and self.bom_id.product_tmpl_id.categ_id.mrp_bom_modification:
            for rec in self:
                if rec.bom_p:
                    rec.product_qty = (rec.bom_p * self.bom_id.product_qty) / 100
        return

    @api.multi
    def compute_bom_p(self):
        pass

    bom_p = fields.Float(
        '% de Lista',
        digits=dp.get_precision('Product Unit of Measure'),
        store=True,
        compute='compute_bom_p',
        inverse='compute_product_qty',
    )
    obligatorio = fields.Boolean(
        'Obligatorio',
        track_visibility='onchange',
    )
    formula_p = fields.Float(
        '% de Formula',
        digits=dp.get_precision('Product Unit of Measure'),
        track_visibility='onchange',
    )


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def write(self, vals):
        msg = ''
        if 'bom_line_ids' in vals:
            for line in vals['bom_line_ids']:
                new_line = False
                line_id = line[1]
                if line_id is False and line[0] == 0:
                    msg = msg + 'Nueva linea: <br/>'
                    new_line = True
                elif line[0] == 2:
                    del_line = self.env['mrp.bom.line'].search([('id', '=', line_id)])
                    product_name = ''
                    if del_line:
                        product_name = del_line.product_id and del_line.product_id.name or ''
                    msg = msg + 'Linea eliminada: <br/>'
                    msg = msg + 'Producto: ' + product_name + '<br/>'
                if line[2]:
                    del_line = self.env['mrp.bom.line'].search([('id', '=', line_id)])
                    product_name = ''
                    if del_line:
                        product_name = del_line.product_id and del_line.product_id.name or ''
                    if new_line is False:
                        msg = msg + 'Linea modificada (' + product_name + '): <br/>'
                    for field in line[2]:
                        new_val = line[2][field]
                        readable_field = field  # USER READABLE NAME
                        if field == 'product_qty':
                            readable_field = 'Cantidad Producto'
                        if field == 'bom_p':
                            readable_field = '% de lista'
                        if field == 'obligatorio':
                            readable_field = 'Obligatorio'
                        if field == 'formula_p':
                            readable_field = '% de Formula'
                        if field == 'attribute_value_ids':
                            readable_field = 'Variantes'
                        if field == 'product_uom_id':
                            readable_field = 'Unidad de medida'
                            uom = self.env['product.uom'].search([('id', '=', line[2][field])])
                            new_val = uom.name
                        if field == 'operation_id':
                            readable_field = 'Consumido en la operacion'
                            operation = self.env['mrp.routing.workcenter'].search([('id', '=', line[2][field])])
                            new_val = operation.name
                        if field == 'product_id':
                            readable_field = 'Producto'
                            product = self.env['product.product'].search([('id', '=', line[2][field])])
                            new_val = product.name
                        msg = msg + readable_field + ': ' + str(new_val) + '<br/>'
        # SE CALCULA EL PORCENTAJE DE CADA LINEA (SOLO PARA PRODUCTOS DE CATEGORIAS CON CHECKBOX MARCADO)
        if self.product_tmpl_id and self.product_tmpl_id.categ_id and self.product_tmpl_id.categ_id.mrp_bom_modification:
            deleted_ids = [line[1] for line in vals.get('bom_line_ids', []) if line[0] == 2]
            modified_ids = [line[1] for line in vals.get('bom_line_ids', []) if line[2]]
            old_values = [line.bom_p for line in self.bom_line_ids if line.id not in modified_ids and line.id not in deleted_ids]
            new_values = [line[2]['bom_p'] for line in vals.get('bom_line_ids', []) if line[2] and 'bom_p' in line[2]]
            bom_p_total = sum(new_values) + sum(old_values)
            if bom_p_total > 100:
                raise ValidationError(_('El % de lista no puede ser mayor al 100%'))
        self.message_post(body=msg, type="comment")
        # revisa que se junte el 100% en la lista de materiales
        res = super(MrpBom, self).write(vals)
        if 'product_qty' in vals:
            for line in self.bom_line_ids:
                line.compute_product_qty()
        return res

    def _get_default_product_uom_id(self):
        return super(MrpBom, self)._get_default_product_uom_id()
    # SE SOBRESCRIBEN LOS CAMPOS PARA AGREGAR EL LOG DE CAMBIOS
    location_src_id = fields.Many2one(
        'stock.location',
        'Source Location',
        help="Location where the system will look for components.",
        track_visibility='onchange',
    )
    location_dest_id = fields.Many2one(
        'stock.location',
        'Destination Location',
        help="Location where the system will stock the finished products.",
        track_visibility='onchange',
    )

    code = fields.Char(
        'Reference',
        track_visibility='onchange',
    )
    active = fields.Boolean(
        'Active',
        default=True,
        help="If the active field is set to False, it will allow you to hide the bills of material without removing it.",
        track_visibility='onchange',
    )
    type = fields.Selection(
        [
            ('normal', 'Manufacture this product'),
            ('phantom', 'Ship this product as a set of components (kit)')
        ],
        'BoM Type',
        default='normal',
        required=True,
        track_visibility='onchange',
        help="Kit (Phantom): When processing a sales order for this product, the delivery order will contain the raw materials, instead of the finished product.",
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product',
        track_visibility='onchange',
        domain="[('type', 'in', ['product', 'consu'])]",
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        'Product Variant',
        track_visibility='onchange',
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.",
    )
    bom_line_ids = fields.One2many(
        'mrp.bom.line',
        'bom_id',
        'BoM Lines',
        copy=True,
        track_visibility='onchange',
    )
    product_qty = fields.Float(
        'Quantity',
        default=1.0,
        digits=dp.get_precision('Unit of Measure'),
        required=True,
        track_visibility='onchange',
    )
    product_uom_id = fields.Many2one(
        'product.uom',
        'Product Unit of Measure',
        track_visibility='onchange',
        default=_get_default_product_uom_id,
        oldname='product_uom',
        required=True,
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control",
    )
    sequence = fields.Integer(
        'Sequence',
        help="Gives the sequence order when displaying a list of bills of material.",
        track_visibility='onchange',
    )
    routing_id = fields.Many2one(
        'mrp.routing',
        'Routing',
        track_visibility='onchange',
        help="The operations for producing this BoM.  When a routing is specified, the production orders will "
             " be executed through work orders, otherwise everything is processed in the production order itself. ",
    )
    ready_to_produce = fields.Selection(
        [
            ('all_available', 'All components available'),
            ('asap', 'The components of 1st operation')
        ],
        string='Manufacturing Readiness',
        track_visibility='onchange',
        default='asap',
        required=True,
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        'Picking Type',
        domain=[('code', '=', 'mrp_operation')],
        help=u"When a procurement has a ‘produce’ route with a picking type set, it will try to create "
             "a Manufacturing Order for that product using a BoM of the same picking type. That allows "
             "to define procurement rules which trigger different manufacturing orders with different BoMs. ",
        track_visibility='onchange',
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env['res.company']._company_default_get('mrp.bom'),
        required=True,
        track_visibility='onchange',
    )
