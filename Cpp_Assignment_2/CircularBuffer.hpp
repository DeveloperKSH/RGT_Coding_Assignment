// CircularBuffer.hpp
#pragma once
#include <vector>
#include <iterator>
#include <type_traits>
#include <cstddef>
#include <utility>
#include <sstream>
#include <stdexcept>

// 고정 용량 원형 버퍼: 가득 차면 가장 오래된 원소를 덮어씀 (O(1) 연산, 전방 반복자 제공)
template <class T>
class CircularBuffer {
public:
  using value_type      = T;
  using size_type       = std::size_t;
  using difference_type = std::ptrdiff_t;

  // 생성자 (capacity>0 필수)
  explicit CircularBuffer(size_type capacity)
    : cap_(capacity), data_(capacity), start_(0), sz_(0) {
    if (cap_ == 0) throw std::invalid_argument("capacity must be > 0");
  }

  // 기본 특성
  size_type size()     const noexcept { return sz_; }
  size_type capacity() const noexcept { return cap_; }
  bool      empty()    const noexcept { return sz_ == 0; }

  // 가장 오래된 원소 참조
  T&       front()       { ensure_not_empty(); return data_[start_]; }
  const T& front() const { ensure_not_empty(); return data_[start_]; }

  // 가장 최근 원소 참조
  T&       back()       { ensure_not_empty(); return data_[index_from_pos(sz_ - 1)]; }
  const T& back() const { ensure_not_empty(); return data_[index_from_pos(sz_ - 1)]; }

  // 기능 1. 뒤에 삽입 (가득 차면 오래된 원소를 덮고 start_ 이동)
  void push_back(const T& item) {
    auto idx = index_from_pos(sz_);
    data_[idx] = item;
    advance_state_after_write();
  }
  void push_back(T&& item) {
    auto idx = index_from_pos(sz_);
    data_[idx] = std::move(item);
    advance_state_after_write();
  }

  // 기능 2. 앞에서 제거 (가장 오래된 원소 제거)
  void pop_front() {
    ensure_not_empty();
    start_ = next_index(start_);
    --sz_;
  }

  // 기능 3. 물리 인덱스 순서 덤프 (디버깅용)
  std::string dump_index() const {
    std::ostringstream oss;
    for (size_t i = 0; i < cap_; ++i) {
        if (i) oss << ", ";
        oss << data_[i];
    }
    return oss.str();
  }

// Forward Iterator (STL 호환)
private:
  template <bool IsConst>
  class fwd_iter {
    using Buf = typename std::conditional<IsConst, const CircularBuffer, CircularBuffer>::type;
    Buf* buf_ = nullptr;
    size_type pos_ = 0;
  public:
    using iterator_category = std::forward_iterator_tag;
    using difference_type   = std::ptrdiff_t;
    using value_type        = T;
    using reference         = typename std::conditional<IsConst, const T&, T&>::type;
    using pointer           = typename std::conditional<IsConst, const T*, T*>::type;

    fwd_iter() = default;
    fwd_iter(Buf* b, size_type p) : buf_(b), pos_(p) {}

    // begin 기준 pos_번째 논리 원소를 역참조 (원형 인덱싱 보정)
    reference operator*()  const { return buf_->data_[buf_->index_from_pos(pos_)]; }
    pointer   operator->() const { return &(**this); }

    fwd_iter& operator++()    { ++pos_; return *this; }
    fwd_iter  operator++(int) { auto tmp = *this; ++(*this); return tmp; }

    friend bool operator==(const fwd_iter& a, const fwd_iter& b) {
      return a.buf_ == b.buf_ && a.pos_ == b.pos_;
    }
    friend bool operator!=(const fwd_iter& a, const fwd_iter& b) {
      return !(a == b);
    }
  };

private:
  size_type cap_;
  std::vector<T> data_;
  size_type start_;
  size_type sz_;    

  // 내부 유틸: 비어있으면 예외
  void ensure_not_empty() const {
    if (empty()) throw std::out_of_range("circular buffer is empty");
  }

  // 내부 유틸: 다음 물리 인덱스(원형)
  size_type next_index(size_type i) const noexcept { return (i + 1) % cap_; }

  // 내부 유틸: begin() 기준 pos번째의 실제 물리 인덱스
  size_type index_from_pos(size_type pos) const noexcept {
    return (start_ + (pos % cap_)) % cap_;
  }
  
  // 내부 유틸: 쓰기 후 상태 갱신 (가득 차면 start_ 한 칸 전진)
  void advance_state_after_write() noexcept {
    if (sz_ < cap_) ++sz_;
    else start_ = next_index(start_);
  }  

public:
  using iterator       = fwd_iter<false>;
  using const_iterator = fwd_iter<true>;

  // 기능 4. 순회 (가장 오래된 것부터 size()개 전방 순회)
  iterator       begin()       { return iterator(this, 0); }
  iterator       end()         { return iterator(this, sz_); }
  const_iterator begin() const { return const_iterator(this, 0); }
  const_iterator end()   const { return const_iterator(this, sz_); }
};
