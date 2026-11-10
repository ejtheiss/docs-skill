---
title: Onboard a Business
deprecated: false
hidden: false
metadata:
  robots: index
---
The steps below detail the fields and API requests required to onboard a business by creating legal entities for the business and its associated owners and control person, and the linked account.

# Collect Required Information for Business UBO Legal Entities

To determine the information required for onboarding a business please review the [required fields for businesses](https://docs.moderntreasury.com/payments/docs/required-fields-for-businesses) guide. This information can be collected via your application or platform processes and must be submitted to Modern Treasury via API, in a single request as detailed below.

<Callout icon="📘" theme="info">
  If you don't have all of the required information yet, create the legal entity with `"status": "draft"` and update it as you collect more information. Only `legal_entity_type` is required while a legal entity is a draft. The required fields are checked when you submit it, and any fields you include are still validated. Beneficial owners and control persons included inline in `legal_entity_associations` are created as drafts too. Nothing is submitted for verification until you update the business with `"status": "pending"`, which submits it together with its draft children. See [Draft legal entities](https://docs.moderntreasury.com/platform/reference/create-legal-entity#draft-legal-entities).
</Callout>

## Beneficial Owner(s) and Control Person

When creating a legal entity for a business, you will need to include information about the business as well as the beneficial owners and control person.

A beneficial owner is defined as any person(s) or entity with 25% ownership of the business. Beneficial owners are commonly individuals but can also be businesses with large ownership stakes such as a holding company or investment firm.

A control person is defined as an individual that has the power to direct the management, policies, and operations of a company. This is commonly a president, CEO, or other high ranking executive at a corporation. Every business being onboarded is required to designate a control person. This person may also be a beneficial owner but does not need to be.

When submitting a business legal entity the beneficial owner(s) and designated control person will be represented as their own legal entities and will be related to the parent business through [Legal Entity Associations](ref:legal-entity-associations) .

Required information for the beneficial owners and control person are available in the [required fields for businesses guide](https://docs.moderntreasury.com/payments/docs/required-fields-for-businesses#required-fields-for-beneficial-owners-and-control-person).

# Creating the Legal Entity Object

To submit the business for verification you will send a single legal entity creation request that includes all required information for onboarding, including all beneficial owner(s) and control person(s). Once the legal entity request is processed it will be submitted for verification.

The below instructions walk through how to structure the embedded objects within the legal entity and create the request.

## Required Documents for Businesses

Businesses are required to submit a document for proof of address that validates their physical address.

Proof of address documents should adhere to the following guidelines:

* Clearly display the entity's full legal name and address
* Be issued by a reliable and independent source (e.g., government authority, regulated financial institution, or utility provider)
* Be recent, typically dated within the last 3 months, with the exception of EIN letters that can be dated within the last 6 months
* Be complete, legible, and unaltered

Common examples of acceptable proof of address documents include:

* Utility bills in the entity's name (e.g., electricity, water, gas, internet)
* EIN letters
* Bank statements
* Government issued correspondence (e.g., tax registration letters, filings, or official notices)
* Lease agreements for the entity's place of business

Please note that the following are generally not accepted:

* Documents that appear altered, incomplete, or illegible
* Outdated documents beyond the acceptable timeframe
* Documents that do not clearly show the entity's legal name and address
* Invoices or informal documents that are not independently verifiable

<br />

To submit a non-EIN letter proof of address document you will structure a document object within the `documents` array within the legal entity body with a `document_type`  of `proof_of_address`.

To submit an EIN letter as a proof of address you will attach the document to the EIN identification object on the legal entity.

To properly structure each document, you will provide the document in a base64 encoded format while also providing a name for the provided document. See below for an example document structure:

```json Proof of Address (non-EIN Letter)
{
    "documents": [
    {
       "document_type": "proof_of_addres",
       "file_data": "dGVzdA==",
       "filename": "proof_of_address.pdf"
    }
  ]
 }
```
```json EIN Letter
{
   "id_number": "123456789",
   "id_type": "us_ein",
   "issuing_country": "US",
   "documents": [
    {
       "document_type": "ein_letter",
       "file_data": "dGVzdA==",
       "filename": "ein_letter.pdf"
    }


 }
```

## Required Identifications for Businesses

When submitting a business for verification it is required to include an identification number in the form of either an EIN or TIN. The following fields and provided values are required when submitting an EIN or TIN:

```json EIN Identification
{
   "id_number": "123456789",
   "id_type": "us_ein",
   "issuing_country": "US"
 }
```

## Required Identifications for Control Person and Beneficial Owners

The control person and beneficial owners are required to submit an identification number in the form of a social security number for U.S. individuals or a tax ID for non-U.S. individuals. Non-U.S. individuals without a tax ID can instead provide a `passport` or `national_id` identification with its document images.

These submission details will be structured as identification objects and embedded within the legal entity payload. The below examples detail how to structure each identification object.

The below example shows how to create an identification object utilizing an SSN:

```json SSN Identification
{
   "id_number": "123456789",
   "id_type": "us_ssn",
   "issuing_country": "US"
 }
```

## Creating the Business Legal Entity with Associated Legal Entities

To submit the business for verification you will send a single legal entity creation request that includes all required information for both the business and related entities.

To properly structure the request create a top level parent Legal Entity representing the top level business, and embed the related control person and beneficial owner(s) as [Legal Entity Associations](ref:legal-entity-associations) represented as child legal entities within the same request. Once the legal entity request is processed it will be submitted for verification.

When submitting addresses for a business legal entity, you must include two addresses: one with `address_types` of `business` and `primary` set to `true`, and one with `address_types` of `business_registered` and `primary` set to `false`. The `business` address represents the physical operating address of the business, while `business_registered` represents the registered address of the business.

The below example models how to create a top level Legal Entity with a separate control person and beneficial owner. To scale this request to your needs you can add additional beneficial owners.

```bash Business Legal Entity with Beneficial Owner and Control Person
curl --request POST \
     --url https://app.moderntreasury.com/api/legal_entities \
     --header 'content-type: application/json' \
     --data '
{
    "legal_entity_type": "business",
    "date_formed": "1800-01-01",
    "business_name": "Hogwarts",
    "legal_structure": "corporation",
    "phone_numbers": [
      {
        "phone_number": "+14185438090"
      }
    ],
    "business_description": "Wizardry Academy",
    "intended_use": "Payment operations and treasury management",
    "expected_activity_volume": 1000000000,
    "documents":[
      {
        "document_type": "proof_of_address",
        "file_data": "dGVzdA==\n",
        "filename": "proof_of_address.pdf"
      }
    ],
    "addresses": [
      {
        "primary": true,
        "line1": "119 5th Ave",
        "line2": "Suite 600",
        "locality": "New York",
        "region": "NY",
        "postal_code": "10011",
        "country": "US",
        "address_types": ["business"]
      },
      {
        "primary": false,
        "line1": "200 Park Ave",
        "line2": "Suite 100",
        "locality": "New York",
        "region": "NY",
        "postal_code": "10012",
        "country": "US",
        "address_types": ["business_registered"]
      }
    ],
    "identifications": [
      {
        "id_type": "us_ein",
        "issuing_country": "US",
        "id_number": "123456789"
      }
      ],
      "legal_entity_associations": [{
          "relationship_types": ["control_person"],
          "child_legal_entity": {
            "legal_entity_type": "individual",
            "first_name": "Harry",
            "middle_name": "James",
            "last_name": "Potter",
            "date_of_birth": "1990-02-06",
            "email": "harry.potter@hogwarts.com",
            "phone_numbers": [
                { "phone_number": "+14185438090"}
                ],
            "addresses": [
            {
                "line1": "119 5th Ave",
                "line2": "Suite 600",
                "locality": "New York",
                "region": "NY",
                "postal_code": "10003",
                "country": "US",
                "address_types": ["residential"],
                "primary": true
            }
            ],
            "identifications": [
            {
                "id_number": "111111111",
                "id_type": "us_ssn",
                "issuing_country": "US"
            }]}},
            {
            "relationship_types": ["beneficial_owner"],
            "child_legal_entity": {
            "legal_entity_type": "individual",
            "first_name": "Albus",
            "middle_name": "Percival",
            "last_name": "Dumbledore",
            "date_of_birth": "1881-07-01",
            "email": "dumbledore@hogwarts.com",
            "phone_numbers": [
                { "phone_number": "+14185438090"}
                ],
            "addresses": [
            {
                "line1": "119 5th Ave",
                "line2": "Suite 600",
                "locality": "New York",
                "region": "NY",
                "postal_code": "10003",
                "country": "US",
                "address_types": ["residential"],
                "primary": true
            }
            ],
            "identifications": [
            {
                "id_number": "111222333",
                "id_type": "us_ssn",
                "issuing_country": "US"
            }
          ]
        }
      }
    ]
  }'
```

## Using Existing Child Legal Entities

If you have already created the child legal entities (e.g., the beneficial owners or control person) via a previous API call, you do not need to send the full nested body again. Instead, you can reference existing child legal entities by their ID using `child_legal_entity_id` in place of the `child_legal_entity` object.

<Callout icon="💡" theme="info">
  You can only provide one of `child_legal_entity` or `child_legal_entity_id` per association — not both. Use `child_legal_entity_id` when the individual already exists, and `child_legal_entity` when creating a new one inline.
</Callout>

```bash Business Legal Entity with Existing Child Legal Entity IDs
curl --request POST \
     --url https://app.moderntreasury.com/api/legal_entities \
     --header 'content-type: application/json' \
     --data '
{
    "legal_entity_type": "business",
    "date_formed": "1800-01-01",
    "business_name": "Hogwarts",
    "legal_structure": "corporation",
    "phone_numbers": [
      {
        "phone_number": "+14185438090"
      }
    ],
    "business_description": "Wizardry Academy",
    "intended_use": "Payment operations and treasury management",
    "expected_activity_volume": 1000000000,
    "documents":[
      {
        "document_type": "proof_of_address",
        "file_data": "dGVzdA==\n",
        "filename": "proof_of_address.pdf"
      }
    ],
    "addresses": [
      {
        "primary": true,
        "line1": "119 5th Ave",
        "line2": "Suite 600",
        "locality": "New York",
        "region": "NY",
        "postal_code": "10011",
        "country": "US",
        "address_types": ["business"]
      },
      {
        "primary": false,
        "line1": "200 Park Ave",
        "line2": "Suite 100",
        "locality": "New York",
        "region": "NY",
        "postal_code": "10012",
        "country": "US",
        "address_types": ["business_registered"]
      }
    ],
    "identifications": [
      {
        "id_type": "us_ein",
        "issuing_country": "US",
        "id_number": "123456789"
      }
    ],
    "legal_entity_associations": [
      {
        "relationship_types": ["control_person"],
        "child_legal_entity_id": "539c02a0-94b9-47e3-828a-13b394f91151"
      },
      {
        "relationship_types": ["beneficial_owner"],
        "child_legal_entity_id": "420ad384-ae2e-4f4d-84b6-427f8f673bae"
      }
    ]
  }'
```

# Monitor the Legal Entity's Status

After successful creation, the legal entity will be submitted to Modern Treasury for review. During review the legal entity will have a `status` of `pending`. After successful verification the legal entity's `status` will be updated to `active` representing that the legal entity can be utilized to create an account and move money.

To programmatically action on the `status` field we recommend subscribing to [legal entity webhooks](https://docs.moderntreasury.com/platform/reference/legal-entity-webhooks) for each status update event (`activated`, `suspended`, `denied`). Upon legal entity approval you will receive an `activated` webhook. If the legal entity is denied after review you will receive a `denied`webhook. Modern Treasury performs recurring reviews of all legal entity's and as such if an `active` legal entity is flagged for investigation the `status` will be changed to `suspended`and a `suspended` webhook event will be emitted.

See below for example webhook payloads for legal entity status updates:

```json Sample Activated Legal Entity Webhook
{
  "event": "activated",
  "data": {
    "id": "15815c3a-7367-4505-a0a1-d0296359c32a",
    "email": "hogwarts@wizardy.com",
    "object": "legal_entity",
    "prefix": null,
    "status": "active",
    "suffix": null,
    "website": "http://www.hogwarts.com",
    "metadata": {},
    "addresses": [
      {
        "id": "306ed6a3-7173-4ca9-a0d1-5999e8423ae7",
        "line1": "119 5th Ave",
        "line2": "Suite 600",
        "object": "legal_entity_address",
        "region": "NY",
        "country": "US",
        "locality": "New York",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "postal_code": "10011",
        "discarded_at": null,
        "address_types": [
          "business"
        ]
      },
      {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "line1": "200 Park Ave",
        "line2": "Suite 100",
        "object": "legal_entity_address",
        "region": "NY",
        "country": "US",
        "locality": "New York",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "postal_code": "10012",
        "discarded_at": null,
        "address_types": [
          "business_registered"
        ]
      }
    ],
    "documents": [
      {
        "id": "deeeef25-5d02-4eb1-9511-e547c26f3f0b",
        "file": {
          "size": 4,
          "filename": "articles_of_incorporation.pdf",
          "content_type": "application/pdf"
        },
        "object": "document",
        "source": "customer",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:25Z",
        "updated_at": "2026-02-24T18:57:27Z",
        "discarded_at": null,
        "document_type": "articles_of_incorporation",
        "documentable_id": "15815c3a-7367-4505-a0a1-d0296359c32a",
        "document_details": [],
        "documentable_type": "legal_entity"
      },
      {
        "id": "b793b681-d909-481a-8576-97d7ce32eba5",
        "file": {
          "size": 4,
          "filename": "proof_of_address.pdf",
          "content_type": "application/pdf"
        },
        "object": "document",
        "source": "customer",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:25Z",
        "updated_at": "2026-02-24T18:57:27Z",
        "discarded_at": null,
        "document_type": "proof_of_address",
        "documentable_id": "15815c3a-7367-4505-a0a1-d0296359c32a",
        "document_details": [],
        "documentable_type": "legal_entity"
      }
    ],
    "last_name": null,
    "live_mode": false,
    "created_at": "2026-02-24T18:57:25Z",
    "first_name": null,
    "regulators": [],
    "updated_at": "2026-02-24T18:57:31Z",
    "date_formed": "1800-01-01",
    "external_id": null,
    "middle_name": null,
    "risk_rating": null,
    "discarded_at": null,
    "intended_use": "Payment operations and treasury management",
    "bank_settings": null,
    "business_name": "Hogwarts",
    "date_of_birth": null,
    "phone_numbers": [
      {
        "phone_number": "+14185438090"
      }
    ],
    "ticker_symbol": null,
    "preferred_name": null,
    "identifications": [
      {
        "id": "42176f51-633a-4bd7-87e6-47e907ffadfb",
        "object": "identification",
        "id_type": "us_ein",
        "documents": [],
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "issuing_region": null,
        "expiration_date": null,
        "issuing_country": "US"
      }
    ],
    "legal_structure": "corporation",
    "listed_exchange": null,
    "legal_entity_type": "business",
    "compliance_details": null,
    "citizenship_country": null,
    "business_description": null,
    "doing_business_as_names": [],
    "operating_jurisdictions": [
      "USA"
    ],
    "country_of_incorporation": "US",
    "expected_activity_volume": 1000000000,
    "industry_classifications": [],
    "third_party_verification": null,
    "legal_entity_associations": [
      {
        "id": "4e8ffc4c-0977-4189-8ae7-362fd13a2a02",
        "title": null,
        "object": "legal_entity_association",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "child_legal_entity": {
          "id": "420ad384-ae2e-4f4d-84b6-427f8f673bae",
          "email": "dumbledore@hogwarts.com",
          "object": "legal_entity",
          "prefix": null,
          "status": "active",
          "suffix": null,
          "website": null,
          "metadata": {},
          "addresses": [
            {
              "id": "62366852-8a15-43e1-b286-8c8d8cbdb136",
              "line1": "119 5th Ave",
              "line2": "Suite 600",
              "object": "legal_entity_address",
              "region": "NY",
              "country": "US",
              "locality": "New York",
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "postal_code": "10003",
              "discarded_at": null,
              "address_types": [
                "residential"
              ]
            }
          ],
          "documents": [],
          "last_name": "Dumbledore",
          "live_mode": false,
          "created_at": "2026-02-24T18:57:26Z",
          "first_name": "Albus",
          "regulators": [],
          "updated_at": "2026-02-24T18:57:31Z",
          "date_formed": null,
          "external_id": null,
          "middle_name": "Percival",
          "risk_rating": null,
          "discarded_at": null,
          "intended_use": null,
          "bank_settings": null,
          "business_name": null,
          "date_of_birth": "1881-07-01",
          "phone_numbers": [
            {
              "phone_number": "+14185438090"
            }
          ],
          "ticker_symbol": null,
          "preferred_name": null,
          "identifications": [
            {
              "id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
              "object": "identification",
              "id_type": "drivers_license",
              "documents": [
                {
                  "id": "347a28d0-34b7-496a-bcde-6c0b674c023a",
                  "file": {
                    "size": 4,
                    "filename": "license_front.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_front",
                  "documentable_id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
                  "document_details": [],
                  "documentable_type": "identification"
                },
                {
                  "id": "5c6e3ddb-d76d-44b4-81d3-72439fe44429",
                  "file": {
                    "size": 4,
                    "filename": "license_back.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_back",
                  "documentable_id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
                  "document_details": [],
                  "documentable_type": "identification"
                }
              ],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            },
            {
              "id": "6b464f15-12fe-40f1-9c79-1866d9359da1",
              "object": "identification",
              "id_type": "us_ssn",
              "documents": [],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            }
          ],
          "legal_structure": null,
          "listed_exchange": null,
          "legal_entity_type": "individual",
          "compliance_details": null,
          "citizenship_country": null,
          "business_description": null,
          "doing_business_as_names": [],
          "operating_jurisdictions": [],
          "country_of_incorporation": null,
          "expected_activity_volume": null,
          "industry_classifications": [],
          "third_party_verification": null,
          "legal_entity_associations": [],
          "politically_exposed_person": null,
          "primary_social_media_sites": [],
          "wealth_and_employment_details": null
        },
        "relationship_types": [
          "beneficial_owner"
        ],
        "ownership_percentage": null,
        "parent_legal_entity_id": "15815c3a-7367-4505-a0a1-d0296359c32a"
      },
      {
        "id": "dfc4d9ca-d971-4577-8d97-7224754ff556",
        "title": null,
        "object": "legal_entity_association",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "child_legal_entity": {
          "id": "539c02a0-94b9-47e3-828a-13b394f91151",
          "email": "harry.potter@hogwarts.com",
          "object": "legal_entity",
          "prefix": null,
          "status": "active",
          "suffix": null,
          "website": null,
          "metadata": {},
          "addresses": [
            {
              "id": "c6748074-7af5-4594-ac81-0a89870995d6",
              "line1": "119 5th Ave",
              "line2": "Suite 600",
              "object": "legal_entity_address",
              "region": "NY",
              "country": "US",
              "locality": "New York",
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "postal_code": "10003",
              "discarded_at": null,
              "address_types": [
                "residential"
              ]
            }
          ],
          "documents": [],
          "last_name": "Potter",
          "live_mode": false,
          "created_at": "2026-02-24T18:57:26Z",
          "first_name": "Harry",
          "regulators": [],
          "updated_at": "2026-02-24T18:57:31Z",
          "date_formed": null,
          "external_id": null,
          "middle_name": "James",
          "risk_rating": null,
          "discarded_at": null,
          "intended_use": null,
          "bank_settings": null,
          "business_name": null,
          "date_of_birth": "1990-02-06",
          "phone_numbers": [
            {
              "phone_number": "+14185438090"
            }
          ],
          "ticker_symbol": null,
          "preferred_name": null,
          "identifications": [
            {
              "id": "3d8e5b6d-ea8e-4bf1-8007-154d9275cd90",
              "object": "identification",
              "id_type": "passport",
              "documents": [
                {
                  "id": "bb039389-27f3-4386-b530-2dacf3a1deba",
                  "file": {
                    "size": 4,
                    "filename": "passport.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_front",
                  "documentable_id": "3d8e5b6d-ea8e-4bf1-8007-154d9275cd90",
                  "document_details": [],
                  "documentable_type": "identification"
                }
              ],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            }
          ],
          "legal_structure": null,
          "listed_exchange": null,
          "legal_entity_type": "individual",
          "compliance_details": null,
          "citizenship_country": null,
          "business_description": null,
          "doing_business_as_names": [],
          "operating_jurisdictions": [],
          "country_of_incorporation": null,
          "expected_activity_volume": null,
          "industry_classifications": [],
          "third_party_verification": null,
          "legal_entity_associations": [],
          "politically_exposed_person": null,
          "primary_social_media_sites": [],
          "wealth_and_employment_details": null
        },
        "relationship_types": [
          "control_person"
        ],
        "ownership_percentage": null,
        "parent_legal_entity_id": "15815c3a-7367-4505-a0a1-d0296359c32a"
      }
    ],
    "politically_exposed_person": null,
    "primary_social_media_sites": [],
    "wealth_and_employment_details": null
  }

}
```
```json Sample Suspended Legal Entity Webhook
{
  "event": "suspended",
  "data": {
    "id": "15815c3a-7367-4505-a0a1-d0296359c32a",
    "email": "hogwarts@wizardy.com",
    "object": "legal_entity",
    "prefix": null,
    "status": "suspended",
    "suffix": null,
    "website": "http://www.hogwarts.com",
    "metadata": {},
    "addresses": [
      {
        "id": "306ed6a3-7173-4ca9-a0d1-5999e8423ae7",
        "line1": "119 5th Ave",
        "line2": "Suite 600",
        "object": "legal_entity_address",
        "region": "NY",
        "country": "US",
        "locality": "New York",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "postal_code": "10011",
        "discarded_at": null,
        "address_types": [
          "business"
        ]
      },
      {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "line1": "200 Park Ave",
        "line2": "Suite 100",
        "object": "legal_entity_address",
        "region": "NY",
        "country": "US",
        "locality": "New York",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "postal_code": "10012",
        "discarded_at": null,
        "address_types": [
          "business_registered"
        ]
      }
    ],
    "documents": [
      {
        "id": "deeeef25-5d02-4eb1-9511-e547c26f3f0b",
        "file": {
          "size": 4,
          "filename": "articles_of_incorporation.pdf",
          "content_type": "application/pdf"
        },
        "object": "document",
        "source": "customer",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:25Z",
        "updated_at": "2026-02-24T18:57:27Z",
        "discarded_at": null,
        "document_type": "articles_of_incorporation",
        "documentable_id": "15815c3a-7367-4505-a0a1-d0296359c32a",
        "document_details": [],
        "documentable_type": "legal_entity"
      },
      {
        "id": "b793b681-d909-481a-8576-97d7ce32eba5",
        "file": {
          "size": 4,
          "filename": "proof_of_address.pdf",
          "content_type": "application/pdf"
        },
        "object": "document",
        "source": "customer",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:25Z",
        "updated_at": "2026-02-24T18:57:27Z",
        "discarded_at": null,
        "document_type": "proof_of_address",
        "documentable_id": "15815c3a-7367-4505-a0a1-d0296359c32a",
        "document_details": [],
        "documentable_type": "legal_entity"
      }
    ],
    "last_name": null,
    "live_mode": false,
    "created_at": "2026-02-24T18:57:25Z",
    "first_name": null,
    "regulators": [],
    "updated_at": "2026-02-24T18:57:31Z",
    "date_formed": "1800-01-01",
    "external_id": null,
    "middle_name": null,
    "risk_rating": null,
    "discarded_at": null,
    "intended_use": "Payment operations and treasury management",
    "bank_settings": null,
    "business_name": "Hogwarts",
    "date_of_birth": null,
    "phone_numbers": [
      {
        "phone_number": "+14185438090"
      }
    ],
    "ticker_symbol": null,
    "preferred_name": null,
    "identifications": [
      {
        "id": "42176f51-633a-4bd7-87e6-47e907ffadfb",
        "object": "identification",
        "id_type": "us_ein",
        "documents": [],
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "issuing_region": null,
        "expiration_date": null,
        "issuing_country": "US"
      }
    ],
    "legal_structure": "corporation",
    "listed_exchange": null,
    "legal_entity_type": "business",
    "compliance_details": null,
    "citizenship_country": null,
    "business_description": null,
    "doing_business_as_names": [],
    "operating_jurisdictions": [
      "USA"
    ],
    "country_of_incorporation": "US",
    "expected_activity_volume": 1000000000,
    "industry_classifications": [],
    "third_party_verification": null,
    "legal_entity_associations": [
      {
        "id": "4e8ffc4c-0977-4189-8ae7-362fd13a2a02",
        "title": null,
        "object": "legal_entity_association",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "child_legal_entity": {
          "id": "420ad384-ae2e-4f4d-84b6-427f8f673bae",
          "email": "dumbledore@hogwarts.com",
          "object": "legal_entity",
          "prefix": null,
          "status": "suspended",
          "suffix": null,
          "website": null,
          "metadata": {},
          "addresses": [
            {
              "id": "62366852-8a15-43e1-b286-8c8d8cbdb136",
              "line1": "119 5th Ave",
              "line2": "Suite 600",
              "object": "legal_entity_address",
              "region": "NY",
              "country": "US",
              "locality": "New York",
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "postal_code": "10003",
              "discarded_at": null,
              "address_types": [
                "residential"
              ]
            }
          ],
          "documents": [],
          "last_name": "Dumbledore",
          "live_mode": false,
          "created_at": "2026-02-24T18:57:26Z",
          "first_name": "Albus",
          "regulators": [],
          "updated_at": "2026-02-24T18:57:31Z",
          "date_formed": null,
          "external_id": null,
          "middle_name": "Percival",
          "risk_rating": null,
          "discarded_at": null,
          "intended_use": null,
          "bank_settings": null,
          "business_name": null,
          "date_of_birth": "1881-07-01",
          "phone_numbers": [
            {
              "phone_number": "+14185438090"
            }
          ],
          "ticker_symbol": null,
          "preferred_name": null,
          "identifications": [
            {
              "id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
              "object": "identification",
              "id_type": "drivers_license",
              "documents": [
                {
                  "id": "347a28d0-34b7-496a-bcde-6c0b674c023a",
                  "file": {
                    "size": 4,
                    "filename": "license_front.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_front",
                  "documentable_id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
                  "document_details": [],
                  "documentable_type": "identification"
                },
                {
                  "id": "5c6e3ddb-d76d-44b4-81d3-72439fe44429",
                  "file": {
                    "size": 4,
                    "filename": "license_back.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_back",
                  "documentable_id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
                  "document_details": [],
                  "documentable_type": "identification"
                }
              ],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            },
            {
              "id": "6b464f15-12fe-40f1-9c79-1866d9359da1",
              "object": "identification",
              "id_type": "us_ssn",
              "documents": [],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            }
          ],
          "legal_structure": null,
          "listed_exchange": null,
          "legal_entity_type": "individual",
          "compliance_details": null,
          "citizenship_country": null,
          "business_description": null,
          "doing_business_as_names": [],
          "operating_jurisdictions": [],
          "country_of_incorporation": null,
          "expected_activity_volume": null,
          "industry_classifications": [],
          "third_party_verification": null,
          "legal_entity_associations": [],
          "politically_exposed_person": null,
          "primary_social_media_sites": [],
          "wealth_and_employment_details": null
        },
        "relationship_types": [
          "beneficial_owner"
        ],
        "ownership_percentage": null,
        "parent_legal_entity_id": "15815c3a-7367-4505-a0a1-d0296359c32a"
      },
      {
        "id": "dfc4d9ca-d971-4577-8d97-7224754ff556",
        "title": null,
        "object": "legal_entity_association",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "child_legal_entity": {
          "id": "539c02a0-94b9-47e3-828a-13b394f91151",
          "email": "harry.potter@hogwarts.com",
          "object": "legal_entity",
          "prefix": null,
          "status": "suspended",
          "suffix": null,
          "website": null,
          "metadata": {},
          "addresses": [
            {
              "id": "c6748074-7af5-4594-ac81-0a89870995d6",
              "line1": "119 5th Ave",
              "line2": "Suite 600",
              "object": "legal_entity_address",
              "region": "NY",
              "country": "US",
              "locality": "New York",
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "postal_code": "10003",
              "discarded_at": null,
              "address_types": [
                "residential"
              ]
            }
          ],
          "documents": [],
          "last_name": "Potter",
          "live_mode": false,
          "created_at": "2026-02-24T18:57:26Z",
          "first_name": "Harry",
          "regulators": [],
          "updated_at": "2026-02-24T18:57:31Z",
          "date_formed": null,
          "external_id": null,
          "middle_name": "James",
          "risk_rating": null,
          "discarded_at": null,
          "intended_use": null,
          "bank_settings": null,
          "business_name": null,
          "date_of_birth": "1990-02-06",
          "phone_numbers": [
            {
              "phone_number": "+14185438090"
            }
          ],
          "ticker_symbol": null,
          "preferred_name": null,
          "identifications": [
            {
              "id": "3d8e5b6d-ea8e-4bf1-8007-154d9275cd90",
              "object": "identification",
              "id_type": "passport",
              "documents": [
                {
                  "id": "bb039389-27f3-4386-b530-2dacf3a1deba",
                  "file": {
                    "size": 4,
                    "filename": "passport.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_front",
                  "documentable_id": "3d8e5b6d-ea8e-4bf1-8007-154d9275cd90",
                  "document_details": [],
                  "documentable_type": "identification"
                }
              ],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            }
          ],
          "legal_structure": null,
          "listed_exchange": null,
          "legal_entity_type": "individual",
          "compliance_details": null,
          "citizenship_country": null,
          "business_description": null,
          "doing_business_as_names": [],
          "operating_jurisdictions": [],
          "country_of_incorporation": null,
          "expected_activity_volume": null,
          "industry_classifications": [],
          "third_party_verification": null,
          "legal_entity_associations": [],
          "politically_exposed_person": null,
          "primary_social_media_sites": [],
          "wealth_and_employment_details": null
        },
        "relationship_types": [
          "control_person"
        ],
        "ownership_percentage": null,
        "parent_legal_entity_id": "15815c3a-7367-4505-a0a1-d0296359c32a"
      }
    ],
    "politically_exposed_person": null,
    "primary_social_media_sites": [],
    "wealth_and_employment_details": null
  }

}
```
```json Sample Denied Legal Entity Webhook
{
  "event": "denied",
  "data": {
    "id": "15815c3a-7367-4505-a0a1-d0296359c32a",
    "email": "hogwarts@wizardy.com",
    "object": "legal_entity",
    "prefix": null,
    "status": "denied",
    "suffix": null,
    "website": "http://www.hogwarts.com",
    "metadata": {},
    "addresses": [
      {
        "id": "306ed6a3-7173-4ca9-a0d1-5999e8423ae7",
        "line1": "119 5th Ave",
        "line2": "Suite 600",
        "object": "legal_entity_address",
        "region": "NY",
        "country": "US",
        "locality": "New York",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "postal_code": "10011",
        "discarded_at": null,
        "address_types": [
          "business"
        ]
      },
      {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "line1": "200 Park Ave",
        "line2": "Suite 100",
        "object": "legal_entity_address",
        "region": "NY",
        "country": "US",
        "locality": "New York",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "postal_code": "10012",
        "discarded_at": null,
        "address_types": [
          "business_registered"
        ]
      }
    ],
    "documents": [
      {
        "id": "deeeef25-5d02-4eb1-9511-e547c26f3f0b",
        "file": {
          "size": 4,
          "filename": "articles_of_incorporation.pdf",
          "content_type": "application/pdf"
        },
        "object": "document",
        "source": "customer",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:25Z",
        "updated_at": "2026-02-24T18:57:27Z",
        "discarded_at": null,
        "document_type": "articles_of_incorporation",
        "documentable_id": "15815c3a-7367-4505-a0a1-d0296359c32a",
        "document_details": [],
        "documentable_type": "legal_entity"
      },
      {
        "id": "b793b681-d909-481a-8576-97d7ce32eba5",
        "file": {
          "size": 4,
          "filename": "proof_of_address.pdf",
          "content_type": "application/pdf"
        },
        "object": "document",
        "source": "customer",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:25Z",
        "updated_at": "2026-02-24T18:57:27Z",
        "discarded_at": null,
        "document_type": "proof_of_address",
        "documentable_id": "15815c3a-7367-4505-a0a1-d0296359c32a",
        "document_details": [],
        "documentable_type": "legal_entity"
      }
    ],
    "last_name": null,
    "live_mode": false,
    "created_at": "2026-02-24T18:57:25Z",
    "first_name": null,
    "regulators": [],
    "updated_at": "2026-02-24T18:57:31Z",
    "date_formed": "1800-01-01",
    "external_id": null,
    "middle_name": null,
    "risk_rating": null,
    "discarded_at": null,
    "intended_use": "Payment operations and treasury management",
    "bank_settings": null,
    "business_name": "Hogwarts",
    "date_of_birth": null,
    "phone_numbers": [
      {
        "phone_number": "+14185438090"
      }
    ],
    "ticker_symbol": null,
    "preferred_name": null,
    "identifications": [
      {
        "id": "42176f51-633a-4bd7-87e6-47e907ffadfb",
        "object": "identification",
        "id_type": "us_ein",
        "documents": [],
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "issuing_region": null,
        "expiration_date": null,
        "issuing_country": "US"
      }
    ],
    "legal_structure": "corporation",
    "listed_exchange": null,
    "legal_entity_type": "business",
    "compliance_details": null,
    "citizenship_country": null,
    "business_description": null,
    "doing_business_as_names": [],
    "operating_jurisdictions": [
      "USA"
    ],
    "country_of_incorporation": "US",
    "expected_activity_volume": 1000000000,
    "industry_classifications": [],
    "third_party_verification": null,
    "legal_entity_associations": [
      {
        "id": "4e8ffc4c-0977-4189-8ae7-362fd13a2a02",
        "title": null,
        "object": "legal_entity_association",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "child_legal_entity": {
          "id": "420ad384-ae2e-4f4d-84b6-427f8f673bae",
          "email": "dumbledore@hogwarts.com",
          "object": "legal_entity",
          "prefix": null,
          "status": "denied",
          "suffix": null,
          "website": null,
          "metadata": {},
          "addresses": [
            {
              "id": "62366852-8a15-43e1-b286-8c8d8cbdb136",
              "line1": "119 5th Ave",
              "line2": "Suite 600",
              "object": "legal_entity_address",
              "region": "NY",
              "country": "US",
              "locality": "New York",
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "postal_code": "10003",
              "discarded_at": null,
              "address_types": [
                "residential"
              ]
            }
          ],
          "documents": [],
          "last_name": "Dumbledore",
          "live_mode": false,
          "created_at": "2026-02-24T18:57:26Z",
          "first_name": "Albus",
          "regulators": [],
          "updated_at": "2026-02-24T18:57:31Z",
          "date_formed": null,
          "external_id": null,
          "middle_name": "Percival",
          "risk_rating": null,
          "discarded_at": null,
          "intended_use": null,
          "bank_settings": null,
          "business_name": null,
          "date_of_birth": "1881-07-01",
          "phone_numbers": [
            {
              "phone_number": "+14185438090"
            }
          ],
          "ticker_symbol": null,
          "preferred_name": null,
          "identifications": [
            {
              "id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
              "object": "identification",
              "id_type": "drivers_license",
              "documents": [
                {
                  "id": "347a28d0-34b7-496a-bcde-6c0b674c023a",
                  "file": {
                    "size": 4,
                    "filename": "license_front.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_front",
                  "documentable_id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
                  "document_details": [],
                  "documentable_type": "identification"
                },
                {
                  "id": "5c6e3ddb-d76d-44b4-81d3-72439fe44429",
                  "file": {
                    "size": 4,
                    "filename": "license_back.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_back",
                  "documentable_id": "4431a2ab-5a29-45a7-b59a-b2fafbcfa7f6",
                  "document_details": [],
                  "documentable_type": "identification"
                }
              ],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            },
            {
              "id": "6b464f15-12fe-40f1-9c79-1866d9359da1",
              "object": "identification",
              "id_type": "us_ssn",
              "documents": [],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            }
          ],
          "legal_structure": null,
          "listed_exchange": null,
          "legal_entity_type": "individual",
          "compliance_details": null,
          "citizenship_country": null,
          "business_description": null,
          "doing_business_as_names": [],
          "operating_jurisdictions": [],
          "country_of_incorporation": null,
          "expected_activity_volume": null,
          "industry_classifications": [],
          "third_party_verification": null,
          "legal_entity_associations": [],
          "politically_exposed_person": null,
          "primary_social_media_sites": [],
          "wealth_and_employment_details": null
        },
        "relationship_types": [
          "beneficial_owner"
        ],
        "ownership_percentage": null,
        "parent_legal_entity_id": "15815c3a-7367-4505-a0a1-d0296359c32a"
      },
      {
        "id": "dfc4d9ca-d971-4577-8d97-7224754ff556",
        "title": null,
        "object": "legal_entity_association",
        "live_mode": false,
        "created_at": "2026-02-24T18:57:26Z",
        "updated_at": "2026-02-24T18:57:26Z",
        "discarded_at": null,
        "child_legal_entity": {
          "id": "539c02a0-94b9-47e3-828a-13b394f91151",
          "email": "harry.potter@hogwarts.com",
          "object": "legal_entity",
          "prefix": null,
          "status": "denied",
          "suffix": null,
          "website": null,
          "metadata": {},
          "addresses": [
            {
              "id": "c6748074-7af5-4594-ac81-0a89870995d6",
              "line1": "119 5th Ave",
              "line2": "Suite 600",
              "object": "legal_entity_address",
              "region": "NY",
              "country": "US",
              "locality": "New York",
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "postal_code": "10003",
              "discarded_at": null,
              "address_types": [
                "residential"
              ]
            }
          ],
          "documents": [],
          "last_name": "Potter",
          "live_mode": false,
          "created_at": "2026-02-24T18:57:26Z",
          "first_name": "Harry",
          "regulators": [],
          "updated_at": "2026-02-24T18:57:31Z",
          "date_formed": null,
          "external_id": null,
          "middle_name": "James",
          "risk_rating": null,
          "discarded_at": null,
          "intended_use": null,
          "bank_settings": null,
          "business_name": null,
          "date_of_birth": "1990-02-06",
          "phone_numbers": [
            {
              "phone_number": "+14185438090"
            }
          ],
          "ticker_symbol": null,
          "preferred_name": null,
          "identifications": [
            {
              "id": "3d8e5b6d-ea8e-4bf1-8007-154d9275cd90",
              "object": "identification",
              "id_type": "passport",
              "documents": [
                {
                  "id": "bb039389-27f3-4386-b530-2dacf3a1deba",
                  "file": {
                    "size": 4,
                    "filename": "passport.pdf",
                    "content_type": "application/pdf"
                  },
                  "object": "document",
                  "source": "customer",
                  "live_mode": false,
                  "created_at": "2026-02-24T18:57:26Z",
                  "updated_at": "2026-02-24T18:57:27Z",
                  "discarded_at": null,
                  "document_type": "identification_front",
                  "documentable_id": "3d8e5b6d-ea8e-4bf1-8007-154d9275cd90",
                  "document_details": [],
                  "documentable_type": "identification"
                }
              ],
              "live_mode": false,
              "created_at": "2026-02-24T18:57:26Z",
              "updated_at": "2026-02-24T18:57:26Z",
              "discarded_at": null,
              "issuing_region": null,
              "expiration_date": null,
              "issuing_country": "US"
            }
          ],
          "legal_structure": null,
          "listed_exchange": null,
          "legal_entity_type": "individual",
          "compliance_details": null,
          "citizenship_country": null,
          "business_description": null,
          "doing_business_as_names": [],
          "operating_jurisdictions": [],
          "country_of_incorporation": null,
          "expected_activity_volume": null,
          "industry_classifications": [],
          "third_party_verification": null,
          "legal_entity_associations": [],
          "politically_exposed_person": null,
          "primary_social_media_sites": [],
          "wealth_and_employment_details": null
        },
        "relationship_types": [
          "control_person"
        ],
        "ownership_percentage": null,
        "parent_legal_entity_id": "15815c3a-7367-4505-a0a1-d0296359c32a"
      }
    ],
    "politically_exposed_person": null,
    "primary_social_media_sites": [],
    "wealth_and_employment_details": null
  }

}
```

# Respond to Requests for Additional Information

When an automated compliance check fails during business onboarding, Modern Treasury opens a Case on the Legal Entity with one or more pending `requested_actions`. Cases are read-only.

Subscribe to [case webhooks](ref:cases) to receive `case.opened`, `case.updated`, and `case.resolved` events. Fetch open Cases for a Legal Entity with `GET /api/cases?subject_type=legal_entity&subject_id=...`, or retrieve a specific Case with `GET /api/cases/{id}`.

Read each pending requested action's `category`, `field`, `instructions`, and `reasons` to determine what information to provide. Resolve the requested action by updating the Legal Entity with `PATCH /api/legal_entities/{id}` or by uploading the named document with `POST /api/documents` and `documentable_type=legal_entity`. Modern Treasury automatically re-runs the compliance evaluation after either call. When all requested actions are resolved, the Case moves to `resolved`. See [Compliance Cases](ref:case-object) for the complete object and category details.

You can also view a Legal Entity's Cases and their requested actions in the Cases tab of the Legal Entity page in the Modern Treasury dashboard.

The business-relevant requested action categories are:

| Category                                            | Field                       | Check                          |
| :-------------------------------------------------- | :-------------------------- | :----------------------------- |
| `onboarding_business_registry_verification_failure` | `articles_of_incorporation` | Business registry verification |
| `onboarding_tin_check_failure`                      | `ein_letter`                | TIN check                      |
| `onboarding_proof_of_address_failure`               | `proof_of_address`          | Proof of address               |

```json Sample Open Case
{
  "id": "c6f2f4a1-7c8e-4d12-9b35-1a2e3f4c5d67",
  "object": "case",
  "live_mode": false,
  "status": "open",
  "subject_type": "legal_entity",
  "subject_id": "8a1b2c3d-4e5f-6789-ab01-cd234ef56789",
  "requested_actions": [
    {
      "id": "d7e3f5b2-8a9c-4e21-b046-2b3f4d5e6a78",
      "object": "requested_action",
      "live_mode": false,
      "category": "onboarding_business_registry_verification_failure",
      "field": "articles_of_incorporation",
      "instructions": "Upload an articles_of_incorporation document showing the business name, registration number, and address to the legal entity using the documents endpoint.",
      "reasons": [
        "identity_unverified"
      ],
      "created_at": "2026-08-20T20:13:46Z",
      "updated_at": "2026-08-20T20:13:46Z"
    }
  ],
  "resolved_actions": [],
  "created_at": "2026-08-20T20:13:46Z",
  "updated_at": "2026-08-20T20:13:46Z"
}
```

# Link a Counterparty to the Legal Entity

You can link a Legal Entity to a [Counterparty](doc:counterparty-management-overview) by passing `legal_entity_id` when creating the Counterparty:

```json Create Counterparty linked to Legal Entity
{
  "name": "Hogwarts Inc.",
  "legal_entity_id": "<legal_entity_id>"
}
```

If the Counterparty already exists, you can link it by passing `counterparty_id` when creating the Legal Entity:

```json Link existing Counterparty when creating Legal Entity
{
  "legal_entity_type": "business",
  "business_name": "Hogwarts Inc.",
  "counterparty_id": "<counterparty_id>"
}
```

You can also create both in a single API call — see [Creating a Counterparty with a Legal Entity](doc:create-a-counterparty#creating-a-counterparty-with-a-legal-entity).

# Open an Account for the Business

After legal entity activation you can open an account and move money on behalf of your customer. See [Provisioning Accounts](doc:provisioning-accounts) for step-by-step instructions on creating an Internal Account, listening for account activation via webhooks, and provisioning stablecoin wallets.

# Service Provider Legal Entity (Optional)

This section applies to platforms whose customers have customers of their own, which can be businesses or individuals. For example, a software company on your platform onboards its merchants. Modern Treasury calls your customer the *service provider* and your customer's customer the *service customer*.

```mermaid
flowchart LR
  platform["Your platform"] -- serves --> provider["Your customer<br/>(service provider)"]
  provider -- serves --> customer["Your customer's customer<br/>(service customer)"]
```

To onboard a service customer, set `service_provider_legal_entity_id` to the service provider's Legal Entity `id`.

| You're onboarding | `service_provider_legal_entity_id` |
| --- | --- |
| A business you serve directly | Omit |
| A service customer | The service provider's Legal Entity `id` |

Each service customer goes through its own verification.

The service provider must be a business. A service customer can't also be a beneficial owner, control person, or authorized signer of another business.

```json Service Provider Association
{
  "service_provider_legal_entity_id": "<service provider's Legal Entity id>"
}
```

<Callout icon="🚧" theme="warning">
  Service customers are off by default. Contact your Modern Treasury account team to turn them on for your program. Until then, a request that sets `service_provider_legal_entity_id` to one of your customers fails with a `422` error. Once they're on, set the field to your own Legal Entity `id` for businesses you serve directly.
</Callout>
