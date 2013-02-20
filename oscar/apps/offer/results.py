from decimal import Decimal as D


class OfferApplications(object):
    """
    A collection of offer applications and the discounts that they give.
    """
    def __init__(self):
        self.applications = {}

    def __iter__(self):
        return self.applications.values().__iter__()

    def add(self, offer, result):
        if offer.id not in self.applications:
            self.applications[offer.id] = {
                'offer': offer,
                'result': result,
                'name': offer.name,
                'description': result.description,
                'voucher': offer.get_voucher(),
                'freq': 0,
                'discount': D('0.00')}
        self.applications[offer.id]['discount'] += result.discount
        self.applications[offer.id]['freq'] += 1

    @property
    def offer_discounts(self):
        """
        Return basket discounts from offers (but not voucher offers)
        """
        discounts = []
        for application in self.applications.values():
            if not application['voucher'] and application['discount'] > 0:
                discounts.append(application)
        return discounts

    @property
    def voucher_discounts(self):
        """
        Return basket discounts from vouchers.
        """
        discounts = []
        for application in self.applications.values():
            if application['voucher'] and application['discount'] > 0:
                discounts.append(application)
        return discounts

    @property
    def post_order_actions(self):
        """
        Return successful offer applications which didn't lead to a discount
        """
        applications = []
        for application in self.applications.values():
            if not application['discount']:
                applications.append(application)
        return applications

    def offers(self):
        return dict([(a['offer'].id, a['offer']) for a in
                     self.applications.values()])