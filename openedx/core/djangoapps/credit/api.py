""" Contains the APIs for course credit requirements """

from .exceptions import InvalidCreditRequirements
from .models import CreditCourse, CreditRequirement, CreditEligibility
from openedx.core.djangoapps.credit.exceptions import InvalidCreditCourse


def set_credit_requirements(course_key, requirements):
    """Add requirements to given course.

    Args:
        course_key(CourseKey): The identifier for course
        requirements(list): List of requirements to be added

    Example:
        >>> set_credit_requirements(
                "course-v1-edX-DemoX-1T2015",
                [
                    {
                        "namespace": "reverification",
                        "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                        "display_name": "Assessment 1",
                        "criteria": {},
                    },
                    {
                        "namespace": "proctored_exam",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Final Exam",
                        "criteria": {},
                    },
                    {
                        "namespace": "grade",
                        "name": "grade",
                        "display_name": "Grade",
                        "criteria": {"min_grade": 0.8},
                    },
                ])

    Raises:
        InvalidCreditRequirements

    Returns:
        None
    """

    invalid_requirements = _validate_requirements(requirements)
    if invalid_requirements:
        invalid_requirements = ", ".join(invalid_requirements)
        raise InvalidCreditRequirements(invalid_requirements)

    try:
        credit_course = CreditCourse.get_credit_course(course_key=course_key)
    except CreditCourse.DoesNotExist:
        raise InvalidCreditCourse()

    old_requirements = CreditRequirement.get_course_requirements(course_key=course_key)
    requirements_to_disable = _get_requirements_to_disable(old_requirements, requirements)
    if requirements_to_disable:
        CreditRequirement.disable_credit_requirements(requirements_to_disable)

    for requirement in requirements:
        CreditRequirement.add_or_update_course_requirement(credit_course, requirement)


def get_credit_requirements(course_key, namespace=None):
    """Get credit eligibility requirements of a given course and namespace.

    Args:
        course_key(CourseKey): The identifier for course
        namespace(str): Namespace of requirements

    Example:
        >>> get_credit_requirements("course-v1-edX-DemoX-1T2015")
                {
                    requirements =
                    [
                        {
                            "namespace": "reverification",
                            "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                            "display_name": "Assessment 1",
                            "criteria": {},
                        },
                        {
                            "namespace": "proctored_exam",
                            "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                            "display_name": "Final Exam",
                            "criteria": {},
                        },
                        {
                            "namespace": "grade",
                            "name": "grade",
                            "display_name": "Grade",
                            "criteria": {"min_grade": 0.8},
                        },
                    ]
                }

    Returns:
        Dict of requirements in the given namespace
    """

    requirements = CreditRequirement.get_course_requirements(course_key, namespace)
    return [
        {
            "namespace": requirement.namespace,
            "name": requirement.name,
            "display_name": requirement.display_name,
            "criteria": requirement.criteria
        }
        for requirement in requirements
    ]


def _get_requirements_to_disable(old_requirements, new_requirements):
    """Get the ids of 'CreditRequirement' entries to be disabled that are
    deleted from the courseware.

    Args:
        old_requirements(QuerySet): QuerySet of CreditRequirement
        new_requirements(list): List of requirements being added

    Returns:
        List of ids of CreditRequirement that are not in new_requirements
    """
    requirements_to_disable = []
    for old_req in old_requirements:
        found_flag = False
        for req in new_requirements:
            # check if an already added requirement is modified
            if req["namespace"] == old_req.namespace and req["name"] == old_req.name:
                found_flag = True
                break
        if not found_flag:
            requirements_to_disable.append(old_req.id)
    return requirements_to_disable


def _validate_requirements(requirements):
    """Validate the requirements.

    Args:
        requirements(list): List of requirements

    Returns:
        List of strings of invalid requirements
    """
    invalid_requirements = []
    for requirement in requirements:
        invalid_params = []
        if not requirement.get("namespace"):
            invalid_params.append("namespace")
        if not requirement.get("name"):
            invalid_params.append("name")
        if not requirement.get("display_name"):
            invalid_params.append("display_name")
        if "criteria" not in requirement:
            invalid_params.append("criteria")

        if invalid_params:
            invalid_requirements.append(
                u"{requirement} has missing/invalid parameters: {params}".format(
                    requirement=requirement,
                    params=invalid_params,
                )
            )
    return invalid_requirements


def get_credit_requests_status(username, course_key):
    """
    Get the credit request status.
    This function returns the status of credit request of user for given course.
    The valid status are 'pending', 'approved' or 'rejected'.

    Args:
        username(str): The username of user
        course_key(CourseKey): The course locator key

    Returns:
        A dictionary of credit user has purchased

    """
    # TODO: Needs Will's work to check the credit user has purchased
    return {}


def _get_duration_and_providers(credit_course):
    """
    Returns the credit providers and eligibility durations.
    The eligibility_duration is the max of the credit duration of
    all the credit providers of given course.

    Args:
        credit_course(CreditCourse): The CreditCourse object

    Returns:
        Tuple of eligibility_duration and credit providers of given course
    """
    providers = credit_course.providers.all()
    seconds_good_for_display = 0
    providers_list = []
    for provider in providers:
        providers_list.append(
            {
                "id": provider.provider_id,
                "display_name": provider.display_name,
                "eligibility_duration": provider.eligibility_duration,
                "provider_url": provider.provider_url
            }
        )
        eligibility_duration = int(provider.eligibility_duration) if provider.eligibility_duration else 0
        seconds_good_for_display = max(eligibility_duration, seconds_good_for_display)

    return seconds_good_for_display, providers_list

def _get_credit_request_status(username, course_key):
    """
    Returns the credit request status

    Args:
        username(str): The username of a user
        course_key(CourseKey): The CourseKey

    Returns:
        The tuple of status and provider\

    """
    status = None
    provider = None
    credit_request = get_credit_requests_status(username, course_key)
    if credit_request:
        status = credit_request["status"]
        provider = credit_request["provider"]
    return status, provider


def get_credit_eligibility(username):
    """
    Returns the all the eligibility the user has meet.

    Args:
        username(str): The username of user

    Example:
        >> get_credit_eligibility('Aamir'):
            {
                "edX/DemoX/Demo_Course": {
                    "created_at": "2015-12-21",
                    "providers": [
                        "id": 12,
                        "display_name": "Arizona State University",
                        "eligibility_duration": 60,
                        "provider_url": "http://arizona/provideere/link"
                    ],
                    "seconds_good_for_display": 90
                }
            }

    Returns:
        A dict of eligibilities
    """
    eligibilities = CreditEligibility.get_user_eligibility(username)
    user_eligibilities = {}
    for eligibility in eligibilities:
        course_key = eligibility.course.course_key
        duration, providers_list = _get_duration_and_providers(eligibility.course)
        user_eligibilities[unicode(course_key)] = {
            "is_eligible": True,
            "created_at": eligibility.created,
            "seconds_good_for_display": duration,
            "providers": providers_list,
        }

        # Default status is requirements_meet
        user_eligibilities[unicode(course_key)]["status"] = "requirements_meet"

        credit_request_status, provider = _get_credit_request_status(username, course_key)
        if credit_request_status:
            user_eligibilities[unicode(course_key)]["status"] = credit_request_status
            user_eligibilities[unicode(course_key)]["provider"] = provider

    return user_eligibilities


def get_purchased_credit_courses(username):
    """
    Returns the purchased credit courses.

    Args:
        username(str): Username of the student

    Returns:
        A dict of courses user has purchased from the credit provider after completion

    """
    # TODO: How to track the purchased courses. It requires Will's work for credit provider integration
    return {}
