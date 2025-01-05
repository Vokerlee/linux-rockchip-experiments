#include "pmu_events.hpp"

#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <inttypes.h>
#include <sys/ioctl.h>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <iostream>

namespace PMU
{

Event::Event(pid_t pid, EventDescriptor event, int group_fd)
{
    const int saved_errno = errno;
    errno = 0;
    event_ = event;

    struct perf_event_attr hw_event;
    memset(&hw_event, 0, sizeof(hw_event));
    hw_event.type           = event_.type;
    hw_event.size           = sizeof(hw_event);
    hw_event.config         = event_.perf_id;
    hw_event.exclude_kernel = 1;
    hw_event.disabled       = 1;
    hw_event.exclude_hv     = 1;
    hw_event.read_format    = PERF_FORMAT_GROUP              | PERF_FORMAT_ID |
                              PERF_FORMAT_TOTAL_TIME_RUNNING | PERF_FORMAT_TOTAL_TIME_ENABLED;

    fd_ = syscall(__NR_perf_event_open, &hw_event, pid, -1, group_fd, 0);
    if (fd_ == -1)
        std::cerr << "syscall(__NR_perf_event_open, ...) returned -1: " <<
            strerror(errno) << std::endl;

    if (ioctl(fd_, PERF_EVENT_IOC_ID, &id_) == -1)
        std::cerr << "ioctl() returned -1: " << strerror(errno) << std::endl;

    if (errno == 0)
        errno = saved_errno;
}

Event::~Event()
{
    disable_collection();
}

Event& Event::operator=(Event&& event)
{
    id_ = event.id_;
    fd_ = event.fd_;
    event_ = event.event_;
    event.fd_ = -1;

    return *this;
}

bool Event::enable_collection() const
{
    const int reset_error = ioctl(fd_, PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
    const int enable_error = ioctl(fd_, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
    return !reset_error && !enable_error;
}

bool Event::disable_collection(bool close_event)
{
    if (fd_ < 0)
        return 0;

    int error_status = ioctl(fd_, PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
    if (close_event) {
        close(fd_);
        fd_ = -1;
    }

    return !error_status;
}

int Event::get_fd() const
{
    return fd_;
}

uint64_t Event::get_id() const
{
    return id_;
}

Events::Events(pid_t pid, const std::vector<EventDescriptor>& events)
{
    add_events(pid, events);
}

Events::Events() {}

void Events::add_events(pid_t pid, const std::vector<EventDescriptor>& events)
{
    pid_ = pid;
    events_.push_back(Event(pid_, events[0], -1)); // PMU leader

    for (size_t i = 1; i < events.size(); ++i)
        events_.push_back(Event(pid, events[i], events_[0].get_fd()));

    ioctl(events_[0].get_fd(), PERF_EVENT_IOC_RESET,   PERF_IOC_FLAG_GROUP);
    ioctl(events_[0].get_fd(), PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
}

void Events::clear_events()
{
    events_.clear();
}

size_t Events::get_num_events() const
{
    return events_.size();
}

bool Events::enable_collection() const
{
    return events_[0].enable_collection();
}

bool Events::disable_collection(bool close_events)
{
    if (close_events == true) {
        int error_status = 0;
        for (auto& event: events_)
            error_status += event.disable_collection(close_events);

        return !error_status;
    }
    else
        return events_[0].disable_collection();
}

std::vector<float> Events::read_events() const
{
    EventsReadFormat reader = {};

    ssize_t num_read_bytes = read(events_[0].get_fd(), &reader, sizeof(reader));
    if (num_read_bytes <= 0)
        return std::vector<float>(0);

    std::vector<float> values;

    for (auto& event: events_) {
        for (size_t i = 0; i < reader.rd_format.num_events; i++) {
            if (reader.rd_format.values[i].id == event.get_id()) {
                values.push_back((float) reader.rd_format.values[i].value);
                break;
            }
        }
    }

    values.push_back((float) reader.rd_format.time_running);
    values.push_back((float) reader.rd_format.time_enabled);

    enable_collection();

    return values;
}

} // namespace PMU
