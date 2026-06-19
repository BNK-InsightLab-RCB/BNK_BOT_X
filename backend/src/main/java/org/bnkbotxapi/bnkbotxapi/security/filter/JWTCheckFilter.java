package org.bnkbotxapi.bnkbotxapi.security.filter;

import io.jsonwebtoken.Claims;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.bnkbotxapi.bnkbotxapi.account.domain.AccountRole;
import org.bnkbotxapi.bnkbotxapi.security.auth.CustomUserPrincipal;
import org.bnkbotxapi.bnkbotxapi.security.util.JWTUtil;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@RequiredArgsConstructor
public class JWTCheckFilter extends OncePerRequestFilter {

    private final JWTUtil jwtUtil;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            try {
                Claims claims = jwtUtil.validate(header.substring(7));
                Long accountId = claims.get("accountId", Long.class);
                String loginId = claims.getSubject();
                String name = claims.get("name", String.class);
                AccountRole role = AccountRole.valueOf(claims.get("role", String.class));
                CustomUserPrincipal principal = new CustomUserPrincipal(accountId, loginId, name, role);
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
                SecurityContextHolder.getContext().setAuthentication(authentication);
            } catch (Exception ignored) {
                SecurityContextHolder.clearContext();
            }
        }
        filterChain.doFilter(request, response);
    }
}
