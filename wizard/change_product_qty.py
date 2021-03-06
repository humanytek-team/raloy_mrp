# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    @api.multi
    def change_prod_qty(self):
        res = super(ChangeProductionQty, self).change_prod_qty()
        # SE RECALCULAN LAS CANTIDADES DE LOS PRODUCTOS A CONSUMIR BASADO EN LA COLUMNA '% REAL'
        for wizard in self:
            if wizard.mo_id.product_id.categ_id.mrp_bom_modification:
                production = wizard.mo_id
                for move in production.move_raw_ids:
                    move.compute_uom_qty()
            for workorder in wizard.mo_id.workorder_ids:
                workorder._onchange_qty_producing()
        return res
