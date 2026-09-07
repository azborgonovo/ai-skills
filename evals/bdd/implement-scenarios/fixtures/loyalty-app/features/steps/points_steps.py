from behave import given, then, when

from src.loyalty import Member, Purchase


@given("Ada is a loyalty member")
def step_ada_is_a_member(context):
    context.member = Member(name="Ada")


@given("Ada has a purchase of {euros:d} euros")
def step_ada_has_a_purchase(context, euros):
    context.purchase = Purchase(euros=euros)


@when("the purchase is completed")
def step_the_purchase_is_completed(context):
    context.member.award_points(context.purchase)


@then("Ada has {points:d} loyalty points")
def step_ada_has_points(context, points):
    assert context.member.points == points
