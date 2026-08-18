from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from agreements.models import Agreement, AgreementNotice
from conflicts.models import CaseUpdate, ConflictCase
from corridors.models import CorridorNotice, CorridorRoute
from core.models import Activity, Alert, Community, Stakeholder
from trade.models import TradeOffer


class Command(BaseCommand):
    help = "Seed PeaceLink with South Sudan demo data."

    def handle(self, *args, **options):
        communities = {}
        for data in [
            ("Bor Dinka Farmers", "Dinka", "Jonglei", "Bor East", "Sector 4", 82),
            ("Twic Pastoralists", "Dinka", "Jonglei", "Twic East", "Northern route", 76),
            ("Bentiu Market", "Nuer", "Unity State", "Rubkona", "Market ward", 68),
            ("Malakal Women's Co-op", "Shilluk", "Upper Nile", "Malakal", "Nile sector", 73),
            ("Pibor Co-op", "Murle", "Jonglei", "Pibor", "Central", 44),
        ]:
            community, _ = Community.objects.update_or_create(
                name=data[0],
                defaults={"ethnic_group": data[1], "county": data[2], "payam": data[3], "boma": data[4], "trust_score": data[5]},
            )
            communities[data[0]] = community

        User = get_user_model()
        node, _ = User.objects.get_or_create(
            username="node",
            defaults={
                "first_name": "Nyakim",
                "last_name": "Gatluak",
                "email": "node@peacelink.local",
                "phone": "+211920000001",
                "role": User.Role.NODE,
                "community": communities["Bor Dinka Farmers"],
            },
        )
        node.set_password("PeaceLink2026!")
        node.save()

        member, _ = User.objects.get_or_create(
            username="member",
            defaults={
                "first_name": "Akol",
                "last_name": "Deng",
                "email": "member@peacelink.local",
                "phone": "+211920000002",
                "role": User.Role.MEMBER,
                "community": communities["Twic Pastoralists"],
            },
        )
        member.set_password("PeaceLink2026!")
        member.save()

        stakeholders = []
        for data in [
            ("government", "Mr Wani Godfrey", "Yei River County Commissioner", "County Administration", "wanigod@gmail.com", "+211920000100"),
            ("ngo", "MCC Peace Desk", "Peacebuilding focal point", "MCC", "peace@mcc.local", "+211920000101"),
            ("community_leader", "Chief Makuei", "Paramount Chief", "Bor East", "", "+211920000102"),
            ("religious_leader", "Rev. Mary Nyaluak", "Church mediator", "Interchurch Forum", "mary@peace.local", "+211920000103"),
        ]:
            stakeholder, _ = Stakeholder.objects.update_or_create(
                name=data[1],
                defaults={"stakeholder_type": data[0], "designation": data[2], "organization": data[3], "email": data[4], "phone": data[5]},
            )
            stakeholders.append(stakeholder)

        route, _ = CorridorRoute.objects.update_or_create(
            name="Northern Bor corridor via Sector 4",
            defaults={
                "origin": communities["Twic Pastoralists"],
                "destination": communities["Bor Dinka Farmers"],
                "description": "Seasonal livestock movement route requiring notice before arrival near sorghum fields.",
                "risk_level": "medium",
            },
        )

        TradeOffer.objects.get_or_create(
            owner=member,
            commodity="Sorghum",
            defaults={
                "community": communities["Bor Dinka Farmers"],
                "category": "grain",
                "quantity": "200 kg",
                "offer_type": "sell",
                "location": "Bor Market",
                "contact_method": "USSD callback",
                "description": "Clean sorghum available for community trade.",
            },
        )
        notice, _ = CorridorNotice.objects.get_or_create(
            route=route,
            herd_group="Twic Dinka Herd Group",
            defaults={"submitted_by": member, "cattle_count": 350, "arrival_date": date.today() + timedelta(days=3), "message": "Herd will follow the northern corridor and requests community acknowledgment."},
        )
        case, _ = ConflictCase.objects.get_or_create(
            case_id="ADR-0001",
            defaults={
                "reporter": member,
                "reporter_name": "Akol Deng",
                "reporter_contact": "+211920000002",
                "community_a": communities["Twic Pastoralists"],
                "community_b": communities["Bor Dinka Farmers"],
                "conflict_type": "crop_damage",
                "severity": "medium",
                "description": "Approximately three acres of sorghum were damaged after a route change.",
                "assigned_node": node,
                "stage": "mediating",
            },
        )
        CaseUpdate.objects.get_or_create(case=case, stage="mediating", defaults={"author": node, "note": "Mediation session scheduled with chiefs and farmer representatives."})

        agreement, _ = Agreement.objects.get_or_create(
            agreement_id="PL-2026-0001",
            defaults={
                "entered_by": node,
                "community_a": communities["Bor Dinka Farmers"],
                "community_b": communities["Twic Pastoralists"],
                "dispute_types": ["resource_access", "land_boundary"],
                "date_signed": date.today(),
                "signing_location": "Bor East Payam office",
                "mediators": "Chief Makuei; MCC Peace Desk",
                "key_terms": ["shared_access", "early_warning"],
                "detailed_terms": "Parties agree to use the marked corridor, share water access, and send early warning notices at least three days before movement.",
                "committee_a_name": "Deng Machar",
                "committee_a_contact": "+211920000200",
                "committee_b_name": "Nyakim Gatluak",
                "committee_b_contact": "+211920000201",
                "follow_up_date": date.today() + timedelta(days=90),
                "status": "active",
                "escalation_contact": "County Peace Committee",
            },
        )
        for stakeholder in stakeholders[:2]:
            AgreementNotice.objects.get_or_create(
                agreement=agreement,
                stakeholder=stakeholder,
                defaults={"channel": "email" if stakeholder.email else "sms", "destination": stakeholder.email or stakeholder.phone, "delivery_status": "queued"},
            )

        Alert.objects.get_or_create(title="Corridor notice pending", defaults={"message": str(notice), "level": "watch", "action_url": notice.get_absolute_url()})
        Activity.objects.get_or_create(actor=node, verb="Demo data loaded", detail="PeaceLink South Sudan workspace ready", accent="teal")
        self.stdout.write(self.style.SUCCESS("PeaceLink demo data loaded. Users: node/member, password: PeaceLink2026!"))
