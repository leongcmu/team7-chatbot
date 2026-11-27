import type { Course } from "@eduling/contracts";
import { copy } from "../i18n";
import chat from "../assets/chat.svg";
function safeUrl(url?: string) {
  if (!url) return;
  try {
    const u = new URL(url);
    if (["https:", "http:"].includes(u.protocol)) return u.href;
  } catch {
    /* Invalid links are not rendered. */
  }
}
export function CourseCard({
  course,
  c,
  onCourseClick,
}: {
  course: Course;
  c: typeof copy.en;
  onCourseClick?: (course: Course) => void;
}) {
  return (
    <div className="eduling-course">
      <div className="eduling-course-visual">
        <img width={24} height={24} src={chat} alt="" />
        {course.goal}
      </div>
      <small>{course.level}</small>
      <h2>{course.title}</h2>
      <p>{course.description}</p>
      {course.mock ? (
        <small>{c.fixture}</small>
      ) : (
        safeUrl(course.url) && (
          <a
            href={safeUrl(course.url)}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => onCourseClick?.(course)}
          >
            {c.view} ↗
          </a>
        )
      )}
    </div>
  );
}
