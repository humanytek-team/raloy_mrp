# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class StockMoveLots(models.Model):
    _inherit = 'stock.move.lots'

    quantity_done = fields.Float(
        'Done',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    quantity = fields.Float(
        'To Do',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    lot_produced_qty = fields.Float(
        'Quantity Finished Product',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Informative, not used in matching",
    )


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    @api.depends('densidad', 'product_uom_qty')
    def _compute_kg(self):
        for rec in self:
            if rec.densidad and rec.product_uom_qty:
                rec.kilos = rec.densidad * rec.product_uom_qty

    @api.multi
    def _compute_percent(self):
        for rec in self:
            if rec.state in ('cancel',):
                rec.porcentaje = 0
            else:
                bom_total = rec.get_bom_total()
                if bom_total > 0 and rec.state not in ('cancel'):
                    rec.porcentaje = (rec.quantity_done * 100) / bom_total

    @api.multi
    def compute_bom_data(self):
        for rec in self:
            if rec.bom_line_id and not rec.new_bom_line:
                rec.obligatorio = rec.bom_line_id.obligatorio
                rec.formula_p = rec.bom_line_id.formula_p
        return

    def get_bom_total(self):
        """OBTIENE EL TOTAL DE MATERIALES DE LA LISTA DE MATERIALES ORIGINAL."""
        bom_total = 0
        if self.raw_material_production_id and self.raw_material_production_id.bom_id \
                and self.raw_material_production_id.bom_id.bom_line_ids:
            bom_total = sum([((line.product_qty / self.raw_material_production_id.bom_id.product_qty)
                              * self.raw_material_production_id.product_qty)
                             for line in self.raw_material_production_id.bom_id.bom_line_ids])
        return bom_total

    # CALCULA EN BASE AL 100% DE LA CANTIDAD A PRODUCIR
    @api.multi
    def compute_uom_qty(self):
        for rec in self:
            new_product_uom_qty = 0
            if rec.raw_material_production_id:
                if rec.real_p >= 0:
                    product_qty = rec.raw_material_production_id.product_qty
                    new_product_uom_qty = ((rec.real_p * product_qty) / 100)
                rec.product_uom_qty = new_product_uom_qty
        return

    @api.multi
    def compute_real_p(self):
        pass

    quantity_done_store = fields.Float(
        'Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    product_uom_qty_original = fields.Float(
        'A consumir (original)',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    unit_factor = fields.Float(
        'Unit Factor',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    obligatorio = fields.Boolean(
        'Obligatorio',
        compute='compute_bom_data',
    )
    formula_p = fields.Float(
        '% de Formula',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='compute_bom_data',
    )
    real_p = fields.Float(
        '% Real',
        digits=dp.get_precision('Product Unit of Measure'),
        store=True,
        compute='compute_real_p',
        inverse='compute_uom_qty',
    )
    densidad = fields.Float(
        'Densidad',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    kilos = fields.Float(
        'Kilos',
        compute='_compute_kg',
        store=True,
        digits=dp.get_precision('Product Unit of Measure'),
    )
    porcentaje = fields.Float(
        '% de Produccion',
        compute='_compute_percent',
        digits=dp.get_precision('Product Unit of Measure'),
    )

    @api.multi
    def action_consume_cancel_window(self):
        ctx = dict(self.env.context)
        self.ensure_one()
        view = self.env.ref('raloy_mrp.view_stock_move_cancel')
        result = {
            'name': _('Cancelar'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
        }
        return result
