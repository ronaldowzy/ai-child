# Opening Greeting v2 Policy v0.1

## 1. Scope

E2-A covers the backend Opening Policy Foundation and minimal runtime wiring.
It converts relationship memory, time context, parent policy, and healthy-use
rules into a structured `OpeningPolicy` used by both fallback text and model
prompt composition.

## 2. Non-goals

- No Android UI/runtime change.
- No push notifications or retention mechanics.
- No Growing Nest.
- No CameraX.
- No DB schema or Alembic migration.
- No full Opening v2 productization or device QA claim.

## 3. Priority

Opening policy follows this priority:

1. Child safety, privacy, and explicit conversation boundary.
2. Bedtime low-stimulation closure and healthy use.
3. Current child state hints.
4. Recent low-sensitivity interest seed.
5. Parent goals translated into low-pressure support.
6. Default light greeting.

The opening should act like a gentle doorway: the child can talk, switch topics,
listen briefly, stop, or go to parents.

## 4. Modes

- `default_light`: no strong context; short invitation.
- `interest_callback`: one low-sensitivity topic can be lightly recalled.
- `boundary_respect`: a recent topic boundary suppresses old-topic recall.
- `bedtime_closure`: short low-stimulation bedtime opening.
- `bedtime_defer_interest`: exciting topic exists but is deferred to daytime.
- `parent_bridge_light`: lightly connects to parents without pressure.
- `low_expression_support`: allows one-word or incomplete expression.

## 5. Interest Recall

Interest recall is allowed only when:

- memory is `MemoryType.INTEREST`;
- `relationship_memory_type == interest_seed`;
- sensitivity is `LOW`;
- memory is active;
- current time is not bedtime closure;
- no active boundary suppresses the topic;
- this process has not just recalled the same child/topic.

The wording must be light and skippable, for example:

```text
豆豆，我记得你提过跑步比赛。今天想聊它，还是换个轻松的？
```

## 6. Boundary Cooldown

`topic_boundary` memory is read from existing relationship memory metadata.

- `topic_change`: suppresses interest callback for the next few process-local
  openings.
- `bedtime_close`: next opening does not automatically continue the old topic.
- `refusal`: suppresses the topic until the child actively brings it back in a
  later design.

No DB field is added in E2-A; the cooldown tracker is process-local.

## 7. Bedtime

When `TimePeriod.BEDTIME`:

- do not expand interest;
- defer exciting topics such as running competitions, games, dinosaur battles,
  adventure stories, challenges, tasks, or rewards;
- prefer parent bridge and rest;
- keep text short.

Forbidden bedtime pulls include: “明天有惊喜”, “一定要回来”, “再聊一会儿”,
“完成一个挑战再睡”, and “偷偷再说一句”.

## 8. Parent Goal Translation

Parent goals do not override child agency or boundaries.

- Learning goals become: “only if the child brings it up, offer one small
  question or help split it into a step.”
- Sleep goals become low-stimulation closure.
- “Do not ask/check school” is transformed into place-neutral prompt rules and
  must not produce school check-in wording.

## 9. Age Bands

No schema change is introduced. The builder reads optional
`communication_preferences.child_age` or `age_band`.

- `age_5_6`: `max_chars=36`, `max_spoken_options=2`, concrete wording.
- `age_7_8`: `max_chars=48`, `max_spoken_options=2`.
- `age_9_10`: `max_chars=60`, `max_spoken_options=3`.
- `unknown`: conservative short wording.

## 10. Forbidden Phrases

Opening policy carries a unified forbidden list, including:

```text
小白狐想你了
你昨天没来
我一直等你
你终于来了
你不来我会难过
只有小白狐懂你
这是我们的小秘密
不要告诉爸爸妈妈
每天都要来
再聊一会儿就有奖励
连续来几天就有惊喜
明天有惊喜
今天必须告诉我一件学校的事
你要多说一点才可以
上次你说过……为什么今天不说了
我们继续上次那个，不要换
```

Fallback opening rejects these phrases; model prompt explicitly forbids them.

## 11. Templates

- Default: `{name}我在这里。你可以慢慢说一句，也可以先听小白狐说一句。`
- Interest: `{name}我记得你提过{topic}。今天想聊它，还是换个轻松的？`
- Boundary: `{name}上次那个我们先不聊。今天想说新的，还是让小白狐先讲一句？`
- Bedtime: `{name}晚上好。我们只说一小句，说完就休息。`
- Bedtime defer: `{name}{topic}我们明天白天再慢慢说。现在轻轻收个尾，好吗？`
- Parent bridge: `{name}这句话也可以告诉爸爸妈妈。小白狐先听你说一点点。`

`{name}` is empty when no child nickname/display name exists.

## 12. Test Matrix

Covered by backend tests:

- interest callback with low seed;
- default light without seed;
- topic change, bedtime close, and refusal boundaries;
- bedtime closure and bedtime defer interest;
- no-school parent message;
- learning goal low-pressure translation;
- age 5-6 and 9-10 limits;
- memory read failure fallback;
- OpeningService fallback and model prompt contract;
- TTS failure and same-session cache regressions.

## 13. E2-B Plan

Later E2-B can add durable recall counters, richer child-state signals,
Android QA, and more nuanced parent bridge UI. It should still avoid push
pressure, streaks, FOMO, or exclusive relationship language.
