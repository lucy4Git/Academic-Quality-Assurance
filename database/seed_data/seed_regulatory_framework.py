"""Seed regulatory framework test fixtures — Phase C.

ALL data here is TEST FIXTURE data — clearly labelled.
These are representative stubs, NOT authoritative regulatory text.
Do not treat as legally binding content.

Run: python database/seed_data/seed_regulatory_framework.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / "backend" / ".env")

DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

AUTHORITIES = [
    {
        "code": "CHE-ZA",
        "name": "[TEST FIXTURE] Council on Higher Education",
        "short_name": "CHE",
        "authority_type": "quality_council",
        "jurisdiction": "National",
        "country": "ZA",
        "description": "[TEST FIXTURE] South Africa's quality council for higher education.",
        "official_website": "https://www.che.ac.za",
        "is_external": True,
        "is_internal": False,
        "is_active": True,
        "status": "active",
    },
    {
        "code": "SAQA-ZA",
        "name": "[TEST FIXTURE] South African Qualifications Authority",
        "short_name": "SAQA",
        "authority_type": "qualification_authority",
        "jurisdiction": "National",
        "country": "ZA",
        "description": "[TEST FIXTURE] Oversees NQF implementation in South Africa.",
        "official_website": "https://www.saqa.org.za",
        "is_external": True,
        "is_internal": False,
        "is_active": True,
        "status": "active",
    },
    {
        "code": "DHET-ZA",
        "name": "[TEST FIXTURE] Department of Higher Education and Training",
        "short_name": "DHET",
        "authority_type": "government_department",
        "jurisdiction": "National",
        "country": "ZA",
        "description": "[TEST FIXTURE] Government department overseeing higher education policy.",
        "official_website": "https://www.dhet.gov.za",
        "is_external": True,
        "is_internal": False,
        "is_active": True,
        "status": "active",
    },
    {
        "code": "ECSA-ZA",
        "name": "[TEST FIXTURE] Engineering Council of South Africa",
        "short_name": "ECSA",
        "authority_type": "professional_council",
        "jurisdiction": "National",
        "country": "ZA",
        "description": "[TEST FIXTURE] Professional body for engineering education accreditation.",
        "official_website": "https://www.ecsa.co.za",
        "is_external": True,
        "is_internal": False,
        "is_active": True,
        "status": "active",
    },
]

FRAMEWORKS = [
    {
        "authority_code": "CHE-ZA",
        "code": "CHE-IQA-2024",
        "name": "[TEST FIXTURE] Institutional Quality Assurance Framework 2024",
        "description": (
            "[TEST FIXTURE] Representative stub of CHE IQA requirements. "
            "NOT authoritative regulatory text."
        ),
        "framework_type": "quality_assurance",
        "scope": "institutional",
        "jurisdiction": "ZA",
        "is_mandatory": True,
        "is_public": True,
        "versions": [
            {
                "version_number": "2024.1",
                "version_label": "[TEST FIXTURE] 2024 Edition",
                "status": "active",
                "standards": [
                    {
                        "code": "CHE-IQA-S1",
                        "title": "[TEST FIXTURE] Governance and Management",
                        "description": "Institutional governance structures and quality management.",
                        "sequence": 1,
                        "is_mandatory": True,
                        "criteria": [
                            {
                                "code": "CHE-IQA-S1-C1",
                                "title": "[TEST FIXTURE] Quality Assurance Policy",
                                "description": "Institution has a documented QA policy approved by council.",
                                "is_mandatory": True,
                                "evaluation_method": "document_presence",
                                "requirements": [
                                    {
                                        "code": "CHE-IQA-S1-C1-R1",
                                        "title": "[TEST FIXTURE] QA Policy Document",
                                        "evidence_type": "document",
                                        "minimum_count": 1,
                                    }
                                ],
                            },
                            {
                                "code": "CHE-IQA-S1-C2",
                                "title": "[TEST FIXTURE] Annual Quality Report",
                                "description": "Annual quality report submitted to CHE.",
                                "is_mandatory": True,
                                "evaluation_method": "document_presence",
                                "requirements": [
                                    {
                                        "code": "CHE-IQA-S1-C2-R1",
                                        "title": "[TEST FIXTURE] Annual Quality Report",
                                        "evidence_type": "document",
                                        "minimum_count": 1,
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "code": "CHE-IQA-S2",
                        "title": "[TEST FIXTURE] Teaching and Learning",
                        "description": "Teaching and learning quality standards.",
                        "sequence": 2,
                        "is_mandatory": True,
                        "criteria": [
                            {
                                "code": "CHE-IQA-S2-C1",
                                "title": "[TEST FIXTURE] Module Assessment Plan",
                                "description": "Each module has a documented assessment plan.",
                                "is_mandatory": True,
                                "evaluation_method": "document_presence",
                                "requirements": [
                                    {
                                        "code": "CHE-IQA-S2-C1-R1",
                                        "title": "[TEST FIXTURE] Assessment Plan",
                                        "evidence_type": "document",
                                        "minimum_count": 1,
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ],
    },
    {
        "authority_code": "ECSA-ZA",
        "code": "ECSA-E-2022",
        "name": "[TEST FIXTURE] Engineering Accreditation Criteria 2022",
        "description": (
            "[TEST FIXTURE] Representative stub of ECSA accreditation requirements. "
            "NOT authoritative regulatory text."
        ),
        "framework_type": "accreditation",
        "scope": "programme",
        "jurisdiction": "ZA",
        "is_mandatory": True,
        "is_public": True,
        "versions": [
            {
                "version_number": "2022.1",
                "version_label": "[TEST FIXTURE] 2022 Edition",
                "status": "active",
                "standards": [
                    {
                        "code": "ECSA-E1",
                        "title": "[TEST FIXTURE] Programme Educational Objectives",
                        "description": "Programme has documented educational objectives.",
                        "sequence": 1,
                        "is_mandatory": True,
                        "criteria": [
                            {
                                "code": "ECSA-E1-C1",
                                "title": "[TEST FIXTURE] Graduate Attribute Mapping",
                                "description": "Curriculum mapped to ECSA graduate attributes.",
                                "is_mandatory": True,
                                "evaluation_method": "document_presence",
                                "requirements": [
                                    {
                                        "code": "ECSA-E1-C1-R1",
                                        "title": "[TEST FIXTURE] Graduate Attribute Map",
                                        "evidence_type": "document",
                                        "minimum_count": 1,
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ],
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def seed():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Find a system admin user to act as creator
        admin = await conn.fetchrow(
            "SELECT id FROM users WHERE role::text = 'SYSTEM_ADMIN' LIMIT 1"
        )
        if admin is None:
            print("No system_admin user found — run run_all.py first.")
            return
        admin_id = admin["id"]

        for auth_data in AUTHORITIES:
            existing = await conn.fetchrow(
                "SELECT id FROM regulatory_authorities WHERE code = $1", auth_data["code"]
            )
            if existing:
                print(f"  Authority {auth_data['code']} already exists — skipping.")
                continue
            await conn.execute(
                """
                INSERT INTO regulatory_authorities
                    (id, code, name, short_name, authority_type, jurisdiction, country,
                     description, official_website, is_external, is_internal, is_active,
                     status, created_by_id, updated_by_id, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), $1, $2, $3, $4, $5, $6,
                     $7, $8, $9, $10, $11,
                     $12, $13, $13, now(), now())
                """,
                auth_data["code"], auth_data["name"], auth_data["short_name"],
                auth_data["authority_type"], auth_data["jurisdiction"], auth_data["country"],
                auth_data["description"], auth_data["official_website"],
                auth_data["is_external"], auth_data["is_internal"], auth_data["is_active"],
                auth_data["status"], admin_id,
            )
            print(f"  Created authority: {auth_data['code']}")

        for fw_data in FRAMEWORKS:
            # Resolve authority_id
            auth_row = await conn.fetchrow(
                "SELECT id FROM regulatory_authorities WHERE code = $1", fw_data["authority_code"]
            )
            if auth_row is None:
                print(f"  Authority {fw_data['authority_code']} not found — skipping framework.")
                continue
            authority_id = auth_row["id"]

            existing_fw = await conn.fetchrow(
                "SELECT id FROM quality_frameworks WHERE code = $1", fw_data["code"]
            )
            if existing_fw:
                print(f"  Framework {fw_data['code']} already exists — skipping.")
                continue

            fw_id = await conn.fetchval(
                """
                INSERT INTO quality_frameworks
                    (id, authority_id, institution_id, code, name, description,
                     framework_type, scope, jurisdiction, is_mandatory, is_public,
                     is_active, created_by_id, updated_by_id, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), $1, NULL, $2, $3, $4,
                     $5, $6, $7, $8, $9,
                     TRUE, $10, $10, now(), now())
                RETURNING id
                """,
                authority_id, fw_data["code"], fw_data["name"], fw_data["description"],
                fw_data["framework_type"], fw_data["scope"], fw_data["jurisdiction"],
                fw_data["is_mandatory"], fw_data["is_public"], admin_id,
            )
            print(f"  Created framework: {fw_data['code']}")

            for ver_data in fw_data.get("versions", []):
                ver_id = await conn.fetchval(
                    """
                    INSERT INTO framework_versions
                        (id, framework_id, version_number, version_label, status,
                         created_by_id, updated_by_id, created_at, updated_at)
                    VALUES
                        (gen_random_uuid(), $1, $2, $3, $4,
                         $5, $5, now(), now())
                    RETURNING id
                    """,
                    fw_id, ver_data["version_number"], ver_data["version_label"],
                    ver_data["status"], admin_id,
                )
                print(f"    Created version: {ver_data['version_number']}")

                for std_data in ver_data.get("standards", []):
                    std_id = await conn.fetchval(
                        """
                        INSERT INTO framework_standards
                            (id, framework_version_id, code, title, description, sequence,
                             weight, is_mandatory, is_active, created_by_id, updated_by_id,
                             created_at, updated_at)
                        VALUES
                            (gen_random_uuid(), $1, $2, $3, $4, $5,
                             1.0, $6, TRUE, $7, $7, now(), now())
                        RETURNING id
                        """,
                        ver_id, std_data["code"], std_data["title"],
                        std_data.get("description"), std_data["sequence"],
                        std_data["is_mandatory"], admin_id,
                    )
                    print(f"      Created standard: {std_data['code']}")

                    for crit_data in std_data.get("criteria", []):
                        crit_id = await conn.fetchval(
                            """
                            INSERT INTO framework_criteria
                                (id, standard_id, code, title, description,
                                 evaluation_method, is_mandatory, requires_human_review,
                                 is_active, weight, sequence, created_by_id, updated_by_id,
                                 created_at, updated_at)
                            VALUES
                                (gen_random_uuid(), $1, $2, $3, $4,
                                 $5, $6, FALSE,
                                 TRUE, 1.0, 0, $7, $7, now(), now())
                            RETURNING id
                            """,
                            std_id, crit_data["code"], crit_data["title"],
                            crit_data.get("description"),
                            crit_data["evaluation_method"], crit_data["is_mandatory"],
                            admin_id,
                        )
                        print(f"        Created criterion: {crit_data['code']}")

                        for req_data in crit_data.get("requirements", []):
                            await conn.execute(
                                """
                                INSERT INTO evidence_requirements
                                    (id, criterion_id, code, title, evidence_type,
                                     minimum_count, is_mandatory, created_by_id,
                                     updated_by_id, created_at, updated_at)
                                VALUES
                                    (gen_random_uuid(), $1, $2, $3, $4,
                                     $5, TRUE, $6, $6, now(), now())
                                """,
                                crit_id, req_data["code"], req_data["title"],
                                req_data["evidence_type"], req_data["minimum_count"], admin_id,
                            )
                            print(f"          Created requirement: {req_data['code']}")

        print("\n[TEST FIXTURE] Regulatory framework seed complete.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
