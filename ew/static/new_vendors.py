from . import cfg as ewcfg

vendor_id_fuckenergy_machine = "fuckenergy_machine"
vendor_id_mtndew_machine = "mtndew_machine"

new_vendor_list = [
    EwVendor(
        vendor_id = vendor_id_fuckenergy_machine,
        display_name = "FUCK ENERGY Vending Machine",
        poi = ewcfg.poi_id_711
    ),
    EwVendor(
        vendor_id = vendor_id_mtndew_machine,
        display_name = "MTN DEW Vending Machine",
        poi = ewcfg.poi_id_711
    )
]
