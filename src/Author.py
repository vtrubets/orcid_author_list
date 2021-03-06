#!/usr/bin/env python

import requests as req
from Affiliation import Affiliation
from utilities import remove_duplicates
import functools


@functools.total_ordering
class Author:
    """
    An author on the publication list.
    """

    def _parse_affiliation_response(self, response):
        """
        Parse the ORCID API response into fields to pass into an Affiliation object.
        """
        if response['organization'].get('disambiguated-organization'):
            disambiguated_id = response['organization'].get('disambiguated-organization').get('disambiguated-organization-identifier')
            disambiguation_source = response['organization'].get('disambiguated-organization').get('disambiguation-source')
        else:
            disambiguated_id = ''
            disambiguation_source = ''

        return Affiliation(
            institution_name=response['organization']['name'],
            department=response['department-name'],
            city=response['organization']['address']['city'],
            region=response['organization']['address']['region'],
            country=response['organization']['address']['country'],
            disambiguated_id=disambiguated_id,
            disambiguation_source=disambiguation_source)

    def __init__(self, orcid, affiliations_checker, contributions):
        """
        An author is uniquely identified by their ORCID. All author information
        is drawn from the ORCID database.
        """
        self.orcid = orcid
        self.contributions = contributions

        # hit orcid for the author profile
        try:
            r = req.get(
                'http://pub.orcid.org/v1.2_rc7/{0}/orcid-profile'.format(orcid),
                headers={'Accept': 'application/orcid+json'})
            r.raise_for_status()
        except req.ConnectionError:
            print("Failed to connect to ORCID database: 'http://pub.orcid.org/v1.2_rc7/{0}/orcid-profile'".format(orcid))

        # parse names
        self.givenName = r.json()['orcid-profile']['orcid-bio']['personal-details']['given-names']['value'].title()
        self.familyName = r.json()['orcid-profile']['orcid-bio']['personal-details']['family-name']['value'].title()

        # parse email -- stored as None if email is not marked as primary or if email is not verified
        if r.json().get('orcid-profile').get('orcid-bio').get('contact-details'):
            emails = r.json()['orcid-profile']['orcid-bio']['contact-details']['email']
            primaryEmails = [x for x in emails if (x.get('primary') is True and x.get('verified'))]
            otherEmails = [x for x in emails if (x.get('primary') is False and x.get('verified'))]
            if primaryEmails:
                self.email = primaryEmails[0]
            elif otherEmails:
                self.email = otherEmails
            else:
                self.email = None
        else:
                self.email = None

        # parse affiliations
        if not r.json().get('orcid-profile').get('orcid-activities'):
            print(
                'Author has no recorded and publicly available information. Source: {0}'.format(
                    r.json()['orcid-profile']['orcid-identifier']['uri']))
            self.affiliations = None
        elif not r.json().get('orcid-profile').get('orcid-activities').get('affiliations'):
            print(
                'Author has no recorded and publicly available affiliations. Source: {0}'.format(
                    r.json().get('orcid-profile').get('orcid-identifier').get('uri')))
            self.affiliations = None
        else:
            affiliations_data = r.json()['orcid-profile']['orcid-activities']['affiliations']['affiliation']
            current_affiliations = filter(lambda affiliation: affiliation.get('end-date') is None and affiliation.get('organization'), affiliations_data)

            affiliations = [self._parse_affiliation_response(value) for value in current_affiliations]

            # check against the canonical affiliations
            checked_affiliations = remove_duplicates((affiliations_checker.validate(x) for x in affiliations))
            self.affiliations = [affiliations_checker.guess_department(x) for x in checked_affiliations]

        leaders = ["doug levinson",
                   "naomi wray",
                   "cathryn lewis",
                   "gerome breen",
                   "pat sullivan"]
        if self.givenName.lower() + " " + self.familyName.lower() == "stephan ripke":
            self.group = 1
        elif 'PI' in self.contributions:
            self.group = 3
        elif self.givenName.lower() + " " + self.familyName.lower() in leaders:
            self.group = 4
        else:
            self.group = 2

    def __repr__(self):
        return '{first_name} {family_name}'.format(first_name=self.givenName, family_name=self.familyName)

    def __lt__(self, other):
        """[1] Stephan Ripke
            [2] PGC MDD members
            [3] Study PIs
            [4] Doug Levinson, Naomi Wray, Cathryn Lewis, Gerome Breen, Pat Sullivan
        """
        # are one of you stephan ripke?

        if self.group > other.group:
            return False
        if self.group < other.group:
            return True
        else:
            if self.familyName.lower() > other.familyName.lower():
                return False
            elif self.familyName.lower() < other.familyName.lower():
                return True
            else:
                return False

    def __eq__(self, other):
        """[1] Stephan Ripke
            [2] PGC MDD members
            [3] Study PIs
            [4] Doug Levinson, Naomi Wray, Cathryn Lewis, Gerome Breen, Pat Sullivan
        """
        # are one of you stephan ripke?

        if self.group != other.group:
            return False
        else:
            if self.familyName.lower() == other.familyName.lower():
                return True
            else:
                return False

    # def __cmp__(self, other):
    #     """[1] Stephan Ripke
    #         [2] PGC MDD members
    #         [3] Study PIs
    #         [4] Doug Levinson, Naomi Wray, Cathryn Lewis, Gerome Breen, Pat Sullivan
    #     """
    #     # are one of you stephan ripke?
    #     self_group = self.get_group()
    #     other_group = other.get_group()

    #     if self_group > other_group:
    #         return 1
    #     if self_group < other_group:
    #         return -1
    #     else:
    #         if self.name.lower() > other.name.lower():
    #             return 1
    #         elif self.name.lower() < other.name.lower():
    #             return -1
    #         else:
    #             return 0
